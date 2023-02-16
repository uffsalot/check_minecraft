#!/usr/bin/env python3
from mcstatus import JavaServer
import sys, string, argparse

# Exit statuses recognized by Nagios.
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# Output formatting string.
OUTPUT_OK = "MINECRAFT OK: {0}/{1} players online, {2} ms |players={0};0;0;0;{1} time={2}ms;{3};{4};0.0 "
OUTPUT_LAT_WARNING = "MINECRAFT WARNING: {0}/{1} players online but latency too high ({2} ms) |players={0};0;0;0;{1} time={2}ms;{3};{4};0.0 "
OUTPUT_LAT_CRITICAL = "MINECRAFT CRITICAL: {0}/{1} players online but latency too high ({2} ms) |players={0};0;0;0;{1} time={2}ms;{3};{4};0.0 "
OUTPUT_FULL_WARNING = "MINECRAFT WARNING: {0}/{1} players online, {2} ms |players={0};0;0;0;{1} time={2}ms;{3};{4};0.0 "
OUTPUT_EXCEPTION = "MINECRAFT CRITICAL: {0}"
OUTPUT_UNKNOWN = "MINECRAFT UNKNOWN: Invalid arguments"

def get_server_info(host, port, timeout):
    server = JavaServer(host, port, timeout)
    status = server.status()
    return {'motd': status.description,
            'players': status.players.online,
            'max_players': status.players.max,
            'latency': round(status.latency, 2)}

def main():
    parser = argparse.ArgumentParser(description="This plugin will try to connect to a Minecraft server.");

    parser.add_argument('-H', '--hostname', dest='hostname', metavar='ADDRESS', required=True, help="host name or IP address")
    parser.add_argument('-p', '--port', dest='port', type=int, default=25565, metavar='INTEGER', help="port number (default: 25565)")
    parser.add_argument('-m', '--motd', dest='motd', default='A Minecraft Server', metavar='STRING', help="expected motd in server response (default: A Minecraft Server)")
    parser.add_argument('-f', '--warn-on-full', dest='full', action='store_true', help="generate warning if server is full")
    parser.add_argument('-w', '--warning', dest='warning', type=float, default=100.0, metavar='DOUBLE', help="response time to result in warning status (milliseconds)")
    parser.add_argument('-c', '--critical', dest='critical', type=float, default=200.0, metavar='DOUBLE', help="response time to result in critical status (milliseconds)")
    parser.add_argument('-t', '--timeout', dest='timeout', type=float, default=1.0, metavar='DOUBLE', help="seconds before connection times out (default: 1)")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help="show details for command-line debugging (Nagios may truncate output)")

    # Parse the arguments. If it failes, exit overriding exit code.
    try:
        args = parser.parse_args()
    except SystemExit:
        print(OUTPUT_UNKNOWN)
        sys.exit(STATE_UNKNOWN)

    try:
        info = get_server_info(args.hostname, args.port, args.timeout)
        if str.find(info['motd'], args.motd) > -1:
            # Check if response time is above critical level.
            if args.critical and info['latency'] > args.critical:
                print(OUTPUT_LAT_CRITICAL.format(info['players'], info['max_players'], info['latency'], args.warning, args.critical))
                sys.exit(STATE_CRITICAL)

            # Check if response time is above warning level.
            if args.warning and info['latency'] > args.warning:
                print(OUTPUT_LAT_WARNING.format(info['players'], info['max_players'], info['latency'], args.warning, args.critical))
                sys.exit(STATE_WARNING)

            # Check if server is full.
            if args.full and info['players'] == info['max_players']:
                print(OUTPUT_FULL_WARNING.format(info['players'], info['max_players'], info['latency'], args.warning, args.critical))
                sys.exit(STATE_WARNING)

            print(OUTPUT_OK.format(info['players'], info['max_players'], info['latency'], args.warning, args.critical))
            sys.exit(STATE_OK)

        else:
            print(OUTPUT_EXCEPTION.format("Unexpected MOTD: {0}".format(info['motd']), info['latency'], args.warning, args.critical))
            sys.exit(STATE_WARNING)

    except Exception:
        print(OUTPUT_EXCEPTION.format("Connection Timed out"))
        sys.exit(STATE_CRITICAL)

if __name__ == "__main__":
    main()
