CRLF = '\r\n'

def deserialize(data):
    term = data[0]
    if term == '*':
        return parse_multi_chunked(data)
    elif term == '$':
        return parse_chunked(data)
    elif term == '+':
        return parse_status(data)
    elif term == '-':
        return parse_error(data)
    elif term == ':':
        return parse_integer(data)
    else:
        return parse_inline(data)

def parse_stream(data):
    cursor = 0
    data_len = len(data)
    result = []
    while cursor < data_len:
        pdata = data[cursor:]
        index = pdata.find(CRLF)
        count = int(pdata[1:index])

        cmd = ''
        start = index + len(CRLF)
        for _ in range(count):
            chunk, length = parse_chunked(pdata, start)
            start = length + len(CRLF)
            cmd += ' ' + chunk
        cursor += start
        result.append(cmd.strip())
    return result

def parse_multi_chunked(data):
    index = data.find(CRLF)
    count = int(data[1:index])
    result = []
    start = index + len(CRLF)
    for _ in range(count):
        chunk, length = parse_chunked(data, start)
        start = length + len(CRLF)
        result.append(chunk)
    return result

def parse_chunked(data, start=0):
    index = data.find(CRLF, start)
    if index == -1:
        index = start
    length = int(data[start + 1:index])
    if length == -1:
        if index + len(CRLF) == len(data):
            return None
        else:
            return None, index
    else:
        result = data[index + len(CRLF):index + len(CRLF) + length]
        return result if start == 0 else [result, index + len(CRLF) + length]

def parse_status(data):
    return [True, data[1:]]

def parse_error(data):
    return [False, data[1:]]

def parse_integer(data):
    return [int(data[1:])]

def parse_inline(data):
    return [data[:data.rfind(CRLF)]]

def serialize_string(data):
    return '+{}\r\n'.format(data)

def serialize_error(data):
    return '-{}\r\n'.format(data)

def serialize_integer(data):
    return ':{}\r\n'.format(data)

def serialize_bulk_string(data):
    if data is None:
      return '$-1\r\n'
    else:
      result = []
      result.append('$')
      result.append(str(len(data)))
      result.append(CRLF)
      result.append(data)
      result.append(CRLF)
      return ''.join(result)

def serialize_array(data):
    data = data.split()
    result = []
    result.append('*')
    result.append(str(len(data)))
    result.append(CRLF)
    for d in data:
        result.append('$')
        result.append(str(len(d)))
        result.append(CRLF)
        result.append(d)
        result.append(CRLF)
    return ''.join(result)
