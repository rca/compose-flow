#!/usr/bin/env python3
"""
Get the first running docker service container
"""
import argparse
import logging
import os
import random
import sh
import shlex
import sys
import time

DSR_DOMAIN = os.environ.get('DSR_DOMAIN', '')
DSR_USER = os.environ.get('DSR_USER', '')


class NoContainer(Exception):
    pass


def list_services(args, remainder):
    command = sh.docker(*shlex.split('service ls'))

    services = []

    for line in command.stdout.decode('utf8').splitlines()[1:]:
        line_split = line.split()

        services.append(line_split[1])

    print('\n'.join(sorted(services)))

    return True


def main(args, remainder):
    """
    Executes container

    Args:
        args: parsed command arguments
        remainder: remaining, unparsed args that are passed along to docker command
    """
    if args.service:
        return run_service(args, remainder)
    elif args.list:
        return list_services(args, remainder)
    else:
        sys.exit('a service or the --list option is required')


def run_service(args, remainder):
    command = sh.docker(*shlex.split('service ps --no-trunc --filter desired-state=running {}'.format(
        args.service))
    )

    containers = []

    try:
        output = command.stdout.decode('utf8').splitlines()[1:]

        # check to see there's at least one container listed
        output[0]
    except IndexError:
        raise NoContainer()
    else:
        for item in output:
            if '{}.'.format(args.service) not in item:
                continue

            containers.append(item)

    if args.random:
        line = random.choice(containers)
    else:
        line = containers[args.container]

    if args.list:
        print('all containers:\n')
        for idx, item in enumerate(containers):
            print('\t{}: {}'.format(idx, item))

        print('selected:\n\t{}'.format(line))

        return

    container_info = line.strip()
    container_info_split = container_info.split()

    container_hash = container_info_split[0]
    container_prefix = container_info_split[1]
    container_host = container_info_split[3]

    # print(container_info)

    if container_host.startswith('ip-'):
        container_host = container_host.replace('ip-', '').replace('-', '.')

    if '.' not in container_host and DSR_DOMAIN:
        container_host = '{}.{}'.format(container_host, DSR_DOMAIN)

    host_info = container_host
    if args.user:
        host_info = f'{args.user}@{host_info}'

    command = f'ssh -t {host_info}'
    docker_command = f'docker exec -t -i {container_prefix}.{container_hash} {" ".join(remainder)}'

    if args.sudo:
        docker_command = 'sudo {}'.format(docker_command)

    if not args.ssh:
        command = '{} {}'.format(command, docker_command)
    else:
        sys.stderr.write('docker_command: {}\n'.format(docker_command))

    logging.debug('command={}'.format(command))
    command = command.split()

    os.execvp(command[0], command)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', '-u', default=DSR_USER, help='the user to connect as (default: {})'.format(DSR_USER))
    parser.add_argument('--loglevel', '-l', default='warn', help='log level')
    parser.add_argument('--retries', type=int, default=30, help='number of times to retry')
    parser.add_argument('--ssh', action='store_true', help='ssh to the machine, not the container')
    parser.add_argument('--sudo', action='store_true', help='use sudo to run the docker command remotely')
    parser.add_argument('--list', action='store_true', help='list available containers')
    parser.add_argument('--container', type=int, default=0, help='which numbered container to select, default=0')
    parser.add_argument('--random', action='store_true', help='pick a random matching container')
    parser.add_argument('service', nargs='?', help='The desired service')

    args, remainder = parser.parse_known_args()

    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))

    result = None
    for i in range(args.retries):
        try:
            result = main(args, remainder)
        except NoContainer:
            time.sleep(1.0)
        else:
            break

    if not result:
        sys.exit('No container found for service={}'.format(args.service))
