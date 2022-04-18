MAX_STRING_WIDTH = 35
SPACE_START = 2
MAX_CONSOLE_BOX_WIDTH = MAX_STRING_WIDTH + SPACE_START


def wrap(string, width):
    wrapped_string = ""
    for i in range(0, len(string), width):
        if i >= MAX_STRING_WIDTH:
            wrapped_string += '\n'
            wrapped_string += ' '*SPACE_START
            wrapped_string += string[i:i + width]
        else:
            wrapped_string += string[i:i + width]
    return wrapped_string


def shell_boxing(payload, output_queries=False):
    output_string = ''
    output_string += '┌─' + '─'*MAX_CONSOLE_BOX_WIDTH + '─┐\n'
    payload = payload.replace('\r\n', '\n')
    payload = payload.split('\n')
    for payload_line in payload:
        if not payload_line:
            payload_line = "\r\n"
        payload_line = wrap(payload_line, MAX_STRING_WIDTH)
        for line in payload_line.splitlines():
            output_string += '│ ' + line if (not output_queries) or \
                (output_queries and (line.startswith(' '*SPACE_START) or not line)) \
                else '├─' + line
            diff = MAX_CONSOLE_BOX_WIDTH - len(line)
            output_string += ' '*diff + ' │\n'
    output_string += '└─' + '─'*MAX_CONSOLE_BOX_WIDTH + '─┘'

    return output_string


if __name__ == "__main__":
    PAYLOAD = "HTTP/1.0 200 OK\r\n" + \
        "Date: Fri, 15 Apr 2022 08:30:22 GMT\r\n" +\
        "Content-Type: text/plain\r\n" +\
        "Content-Length: 37\r\n" +\
        "Connection: close\r\n\r\n\r\n" +\
        "a.txt\r\nc.txt\r\nfile1.txt\r\nfolder1\r\nfolder2"
    print(PAYLOAD)
    print(shell_boxing(PAYLOAD))
    print(shell_boxing(PAYLOAD, output_queries=True))
