/* SPDX-License-Identifier: Apache-2.0 */

#include "flyreflex.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>

static pthread_mutex_t g_guard_lock = PTHREAD_MUTEX_INITIALIZER;
static struct flyreflex_output_s g_guard_output;
static uint64_t g_guard_updated;

static uint64_t monotonic_ns(void)
{
  struct timespec timestamp;

  if (clock_gettime(CLOCK_MONOTONIC, &timestamp) != 0)
    {
      return 0;
    }

  return (uint64_t)timestamp.tv_sec * UINT64_C(1000000000) +
         (uint64_t)timestamp.tv_nsec;
}

static int compare_u64(const void *left, const void *right)
{
  uint64_t a = *(const uint64_t *)left;
  uint64_t b = *(const uint64_t *)right;
  return (a > b) - (a < b);
}

/* Observability/Agent interface outside all timed core paths. NuttX flat
 * built-in tasks share this snapshot. No executor or direct motor API exists.
 */
void flyreflex_guard_publish(const struct flyreflex_output_s *output)
{
  pthread_mutex_lock(&g_guard_lock);
  g_guard_output = *output;
  g_guard_updated = monotonic_ns();
  pthread_mutex_unlock(&g_guard_lock);
}

int flyreflex_guard_command(bool issue_forward)
{
  struct flyreflex_output_s output;
  struct flyreflex_arbitration_s result;
  uint64_t updated, now;
  bool fresh;
  pthread_mutex_lock(&g_guard_lock);
  output = g_guard_output;
  updated = g_guard_updated;
  pthread_mutex_unlock(&g_guard_lock);
  now = monotonic_ns();
  fresh = updated != 0 && now >= updated && now - updated <= UINT64_C(1500000000);
  if (!fresh)
    {
      output.input_valid = false;
      output.state = FLYREFLEX_STATE_INVALID;
      output.command = FLYREFLEX_CMD_STOP;
    }
  flyreflex_arbitrate(FLYREFLEX_CMD_FORWARD, &output, &result);
  printf("{\"interface\":\"flyreflex-guard\",\"operation\":\"%s\","
         "\"fresh\":%s,\"state\":\"%s\",\"risk\":%" PRId32
         ",\"reflex\":\"%s\",\"agent\":\"FORWARD\",\"final\":\"%s\","
         "\"decision\":\"%s\",\"actuator\":\"simulation-only\"}\n",
         issue_forward ? "issue_agent_command" : "query_flyreflex_status",
         fresh ? "true" : "false", flyreflex_state_name(output.state),
         output.gf_membrane_milli, flyreflex_command_name(output.command),
         flyreflex_command_name(result.final_command),
         flyreflex_decision_name(result.decision));
  return 0;
}

/* Interactive comparison. Both agents use the same detector and fixed-delay
 * command queue. Only the second agent has immediate reflex arbitration.
 * Input: seq reset delay_ticks size_a rate_a size_b rate_b (25 ms/tick).
 * This is a controlled latency model, NOT an LLM implementation.
 */
int flyreflex_control(void)
{
  struct flyreflex_engine_s engines[2];
  struct flyreflex_output_s outputs[2];
  enum flyreflex_command_e queues[2][41];
  struct flyreflex_arbitration_s result;
  char line[160];
  unsigned int seq, reset, delay, cursor = 0;
  int sa, ra, sb, rb, side;
  memset(queues, 0, sizeof(queues));
  flyreflex_engine_reset(&engines[0]);
  flyreflex_engine_reset(&engines[1]);
  puts("FR2 READY");
  fflush(stdout);
  while (fgets(line, sizeof(line), stdin) != NULL)
    {
      enum flyreflex_command_e agent[2];
      uint64_t start, end;
      if (strncmp(line, "quit", 4) == 0) break;
      if (sscanf(line, "%u %u %u %d %d %d %d", &seq, &reset, &delay,
                 &sa, &ra, &sb, &rb) != 7 || delay > 40 || reset > 1)
        {
          puts("FR2 ERROR");
          fflush(stdout);
          continue;
        }
      if (reset)
        {
          flyreflex_engine_reset(&engines[0]);
          flyreflex_engine_reset(&engines[1]);
          memset(queues, 0, sizeof(queues));
          cursor = 0;
        }
      start = monotonic_ns();
      for (side = 0; side < 2; side++)
        {
          struct flyreflex_input_s input = {side ? sb : sa,
                                            side ? rb : ra, seq};
          flyreflex_engine_step(&engines[side], &input, &outputs[side]);
          queues[side][cursor] = outputs[side].command;
          agent[side] = queues[side][(cursor + 41 - delay) % 41];
          if (agent[side] == FLYREFLEX_CMD_IDLE)
            agent[side] = FLYREFLEX_CMD_FORWARD;
          if (!outputs[side].input_valid) agent[side] = FLYREFLEX_CMD_STOP;
        }
      flyreflex_arbitrate(agent[1], &outputs[1], &result);
      end = monotonic_ns();
      flyreflex_guard_publish(&outputs[1]);
      printf("FR2 {\"source\":\"%s\",\"seq\":%u,\"agent_a\":\"%s\","
             "\"agent_b\":\"%s\",\"action\":\"%s\",\"lplc2\":%" PRId32
             ",\"lc4\":%" PRId32 ",\"gf\":%" PRId32
             ",\"state\":\"%s\",\"latency_ns\":%" PRIu64 "}\n",
#ifdef __NuttX__
             "openvela",
#else
             "host-reference",
#endif
             seq, flyreflex_command_name(agent[0]),
             flyreflex_command_name(agent[1]),
             flyreflex_command_name(result.final_command),
             outputs[1].lplc2_activity_milli, outputs[1].lc4_activity_milli,
             outputs[1].gf_membrane_milli,
             flyreflex_state_name(outputs[1].state), end - start);
      fflush(stdout);
      cursor = (cursor + 1) % 41;
    }
  return 0;
}

/* Presentation pacing is outside the timed safety path. Each line is an
 * actual core result; visual interpolation must never make safety decisions.
 */
int flyreflex_stream(enum flyreflex_scenario_e scenario, unsigned int cycles)
{
  const struct flyreflex_scenario_data_s *data = flyreflex_get_scenario(scenario);
  struct flyreflex_engine_s engine;
  struct flyreflex_input_s input;
  struct flyreflex_output_s output;
  struct flyreflex_arbitration_s arbitration;
  struct timespec delay = {0, 400000000};
  unsigned int cycle;
  size_t frame;
  uint64_t seq = 0;
  if (data == NULL) return 1;
  for (cycle = 0; cycle < cycles; cycle++)
    {
      flyreflex_engine_reset(&engine);
      for (frame = 0; frame < data->count; frame++)
        {
          uint64_t start;
          uint64_t end;
          flyreflex_make_input(data, frame, &input);
          start = monotonic_ns();
          flyreflex_engine_step(&engine, &input, &output);
          flyreflex_arbitrate(FLYREFLEX_CMD_FORWARD, &output, &arbitration);
          end = monotonic_ns();
          flyreflex_guard_publish(&output);
          printf("FR1 {\"schema\":1,\"source\":\"%s\",\"seq\":%" PRIu64
                 ",\"cycle\":%u,\"scenario\":\"%s\",\"frame\":%zu,"
                 "\"count\":%zu,\"size\":%" PRId32 ",\"rate\":%" PRId32
                 ",\"lplc2\":%" PRId32 ",\"lc4\":%" PRId32
                 ",\"gf\":%" PRId32 ",\"state\":\"%s\","
                 "\"ai\":\"FORWARD\",\"action\":\"%s\","
                 "\"decision\":\"%s\",\"latency_ns\":%" PRIu64 "}\n",
#ifdef __NuttX__
                 "openvela",
#else
                 "host-reference",
#endif
                 seq++, cycle, data->name, frame, data->count,
                 input.angular_size_milli, input.angular_rate_milli,
                 output.lplc2_activity_milli, output.lc4_activity_milli,
                 output.gf_membrane_milli, flyreflex_state_name(output.state),
                 flyreflex_command_name(arbitration.final_command),
                 flyreflex_decision_name(arbitration.decision), end - start);
          fflush(stdout);
          nanosleep(&delay, NULL);
        }
    }
  return 0;
}

static void calculate_stats(uint64_t *values, size_t count,
                            struct flyreflex_stats_s *stats)
{
  uint64_t sum = 0;
  size_t index;

  qsort(values, count, sizeof(values[0]), compare_u64);
  for (index = 0; index < count; index++)
    {
      sum += values[index];
    }

  stats->minimum_ns = values[0];
  stats->mean_ns = sum / count;
  stats->median_ns = values[(count - 1) / 2];
  stats->p95_ns = values[((count - 1) * 95) / 100];
  stats->p99_ns = values[((count - 1) * 99) / 100];
  stats->maximum_ns = values[count - 1];
}

const char *flyreflex_command_name(enum flyreflex_command_e command)
{
  static const char *const names[] =
  {
    "IDLE", "FORWARD", "LEFT", "RIGHT", "STOP", "ESCAPE"
  };

  if (command < FLYREFLEX_CMD_IDLE || command > FLYREFLEX_CMD_ESCAPE)
    {
      return "INVALID";
    }

  return names[command];
}

const char *flyreflex_state_name(enum flyreflex_state_e state)
{
  static const char *const names[] =
  {
    "SAFE", "CAUTION", "DANGER", "INVALID"
  };

  if (state < FLYREFLEX_STATE_SAFE || state > FLYREFLEX_STATE_INVALID)
    {
      return "INVALID";
    }

  return names[state];
}

const char *flyreflex_decision_name(enum flyreflex_decision_e decision)
{
  static const char *const names[] =
  {
    "AI", "REFLEX_OVERRIDE", "FAILSAFE"
  };

  if (decision < FLYREFLEX_DECISION_AI ||
      decision > FLYREFLEX_DECISION_FAILSAFE)
    {
      return "INVALID";
    }

  return names[decision];
}

void flyreflex_print_sample(const char *scenario,
                            const struct flyreflex_sample_s *sample, bool csv,
                            bool print_header)
{
  uint64_t reflex_ns;
  uint64_t end_to_end_ns;

  if (sample == NULL)
    {
      return;
    }

  reflex_ns = sample->latency.reflex_end_ns - sample->latency.reflex_start_ns;
  end_to_end_ns = sample->latency.arbiter_end_ns - sample->latency.event_ns;

  if (csv)
    {
      if (print_header)
        {
          printf("scenario,frame,size_milli,rate_milli,lplc2_milli,lc4_milli,"
                 "gf_milli,state,ai_cmd,reflex_cmd,final_cmd,decision,"
                 "reflex_ns,end_to_end_ns\n");
        }

      printf("%s,%" PRIu32 ",%" PRId32 ",%" PRId32 ",%" PRId32
             ",%" PRId32 ",%" PRId32 ",%s,%s,%s,%s,%s,%" PRIu64
             ",%" PRIu64 "\n",
             scenario, sample->input.frame, sample->input.angular_size_milli,
             sample->input.angular_rate_milli,
             sample->reflex.lplc2_activity_milli,
             sample->reflex.lc4_activity_milli,
             sample->reflex.gf_membrane_milli,
             flyreflex_state_name(sample->reflex.state),
             flyreflex_command_name(sample->arbitration.ai_command),
             flyreflex_command_name(sample->arbitration.reflex_command),
             flyreflex_command_name(sample->arbitration.final_command),
             flyreflex_decision_name(sample->arbitration.decision), reflex_ns,
             end_to_end_ns);
      return;
    }

  printf("[FlyReflex] scenario=%s frame=%" PRIu32
         " size=%" PRId32 " rate=%" PRId32
         " LPLC2=%" PRId32 " LC4=%" PRId32 " GF=%" PRId32
         " state=%s ai=%s reflex=%s final=%s decision=%s"
         " reflex_ns=%" PRIu64 " end_to_end_ns=%" PRIu64 "\n",
         scenario, sample->input.frame, sample->input.angular_size_milli,
         sample->input.angular_rate_milli,
         sample->reflex.lplc2_activity_milli,
         sample->reflex.lc4_activity_milli,
         sample->reflex.gf_membrane_milli,
         flyreflex_state_name(sample->reflex.state),
         flyreflex_command_name(sample->arbitration.ai_command),
         flyreflex_command_name(sample->arbitration.reflex_command),
         flyreflex_command_name(sample->arbitration.final_command),
         flyreflex_decision_name(sample->arbitration.decision), reflex_ns,
         end_to_end_ns);
}

int flyreflex_run_scenario(enum flyreflex_scenario_e scenario, bool csv,
                           struct flyreflex_sample_s *samples,
                           size_t sample_capacity, size_t *sample_count)
{
  const struct flyreflex_scenario_data_s *data;
  struct flyreflex_engine_s engine;
  struct flyreflex_sample_s sample;
  size_t index;

  data = flyreflex_get_scenario(scenario);
  if (data == NULL)
    {
      return -1;
    }

  flyreflex_engine_reset(&engine);
  for (index = 0; index < data->count; index++)
    {
      memset(&sample, 0, sizeof(sample));
      flyreflex_make_input(data, index, &sample.input);
      sample.latency.event_ns = monotonic_ns();
      sample.latency.reflex_start_ns = monotonic_ns();
      flyreflex_engine_step(&engine, &sample.input, &sample.reflex);
      sample.latency.reflex_end_ns = monotonic_ns();
      flyreflex_arbitrate(FLYREFLEX_CMD_FORWARD, &sample.reflex,
                          &sample.arbitration);
      sample.latency.arbiter_end_ns = monotonic_ns();
      flyreflex_guard_publish(&sample.reflex);

      if (samples != NULL && index < sample_capacity)
        {
          samples[index] = sample;
        }

      flyreflex_print_sample(data->name, &sample, csv, csv && index == 0);
    }

  if (sample_count != NULL)
    {
      *sample_count = data->count;
    }

  return 0;
}

int flyreflex_run_benchmark(size_t iterations,
                            struct flyreflex_stats_s *reflex_stats,
                            struct flyreflex_stats_s *end_to_end_stats)
{
  struct flyreflex_input_s input = {960, 1000, 0};
  struct flyreflex_engine_s engine;
  struct flyreflex_output_s output;
  struct flyreflex_arbitration_s arbitration;
  uint64_t *reflex_values;
  uint64_t *end_to_end_values;
  uint64_t start;
  uint64_t reflex_end;
  uint64_t arbiter_end;
  size_t index;

  if (iterations == 0 || reflex_stats == NULL || end_to_end_stats == NULL)
    {
      return -1;
    }

  reflex_values = (uint64_t *)malloc(iterations * sizeof(uint64_t));
  end_to_end_values = (uint64_t *)malloc(iterations * sizeof(uint64_t));
  if (reflex_values == NULL || end_to_end_values == NULL)
    {
      free(reflex_values);
      free(end_to_end_values);
      return -1;
    }

  for (index = 0; index < iterations; index++)
    {
      flyreflex_engine_reset(&engine);
      start = monotonic_ns();
      flyreflex_engine_step(&engine, &input, &output);
      reflex_end = monotonic_ns();
      flyreflex_arbitrate(FLYREFLEX_CMD_FORWARD, &output, &arbitration);
      arbiter_end = monotonic_ns();
      reflex_values[index] = reflex_end - start;
      end_to_end_values[index] = arbiter_end - start;
    }

  calculate_stats(reflex_values, iterations, reflex_stats);
  calculate_stats(end_to_end_values, iterations, end_to_end_stats);
  free(reflex_values);
  free(end_to_end_values);
  return 0;
}
