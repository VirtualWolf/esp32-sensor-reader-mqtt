import utime

def log(message, write_to_log=False):
    year, month, day, hour, minute, second, weekday, yearday = utime.gmtime()

    now = '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(year, month, day, hour, minute, second)

    log_line = '[%s] %s' % (now, message)

    if write_to_log:
        print(log_line)

        with open('log', 'a') as f:
            f.write(log_line + '\n')
    else:
        print(log_line)
