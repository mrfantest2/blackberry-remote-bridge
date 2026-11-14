#ifndef TORCHOS_COMMANDS_H
#define TORCHOS_COMMANDS_H
typedef void (*commands_emit_fn)(char);
typedef const char *(*commands_label_fn)(void);
void commands_init(commands_emit_fn out, commands_label_fn machine);
void commands_execute(const char *line);
#endif
