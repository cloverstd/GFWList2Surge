#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import urlparse
import logging
import urllib2
from argparse import ArgumentParser

__all__ = ['main']


gfwlist_url = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', dest='input',
                        help='path to gfwlist', metavar='GFWLIST')
    parser.add_argument('-f', '--file', dest='output', required=False,
                        help='path to output surge conf', metavar='surge.conf')
    parser.add_argument('-p', '--proxy', dest='proxy', required=False,
                        help='the proxy parameter in the pac file, '
                             'for example, "SOCKS5 127.0.0.1:1080;"',
                        metavar='PROXY')
    parser.add_argument('--user-rule', dest='user_rule',
                        help='user rule file, which will be appended to'
                             ' gfwlist')
    parser.add_argument('--surge-proxy-name', dest='proxy_name', required=True,
                        help='Surge Proxy name')
    parser.add_argument('--surge-proxy', dest='surge_proxy', required=True,
                        help='Surge Proxy conf')
    parser.add_argument('--all-tcp-mode', dest='all_tcp_mode', required=False,
                        help='all-tcp-mode defalut false')
    parser.add_argument('-l', '--loglevel', dest='loglevel', required=False,
                        help='loglevel default notify')
    return parser.parse_args()

def get_data_from_file(file_path):
    with open(file_path, 'rb') as f:
        builtin_rules = f.read()
        return builtin_rules


def decode_gfwlist(content):
    # decode base64 if have to
    try:
        if '.' in content:
            raise Exception()
        return content.decode('base64')
    except:
        return content


def get_hostname(something):
    try:
        # quite enough for GFW
        if not something.startswith('http:'):
            something = 'http://' + something
        r = urlparse.urlparse(something)
        return r.hostname
    except Exception as e:
        logging.error(e)
        return None


def add_domain_to_set(s, something):
    hostname = get_hostname(something)
    if hostname is not None:
        s.add(hostname)


def combine_lists(content, user_rule=None):
    # gfwlist = get_data_from_file('resources/builtin.txt').splitlines(False)
    gfwlist = content.splitlines(False)
    if user_rule:
        gfwlist.extend(user_rule.splitlines(False))
    return gfwlist


def parse_gfwlist(gfwlist):
    domains = set()
    for line in gfwlist:
        if line.find('.*') >= 0:
            continue
        elif line.find('*') >= 0:
            line = line.replace('*', '/')
        if line.startswith('||'):
            line = line.lstrip('||')
        elif line.startswith('|'):
            line = line.lstrip('|')
        elif line.startswith('.'):
            line = line.lstrip('.')
        if line.startswith('!'):
            continue
        elif line.startswith('['):
            continue
        elif line.startswith('@'):
            # ignore white list
            continue
        add_domain_to_set(domains, line)
    return domains


def reduce_domains(domains):
    # reduce 'www.google.com' to 'google.com'
    # remove invalid domains
    tld_content = get_data_from_file("resources/tld.txt")
    tlds = set(tld_content.splitlines(False))
    new_domains = set()
    for domain in domains:
        domain_parts = domain.split('.')
        last_root_domain = None
        for i in xrange(0, len(domain_parts)):
            root_domain = '.'.join(domain_parts[len(domain_parts) - i - 1:])
            if i == 0:
                if not tlds.__contains__(root_domain):
                    # root_domain is not a valid tld
                    break
            last_root_domain = root_domain
            if tlds.__contains__(root_domain):
                continue
            else:
                break
        if last_root_domain is not None:
            new_domains.add(last_root_domain)
    return new_domains


def generate_surge(domains, proxy_name, surge_proxy):
    # render the surge.conf file
    surge_conf_content = get_data_from_file('resources/surge.conf')
    rule = list()
    rule_tpl = "DOMAIN-SUFFIX,{domain},{proxy_name}"
    for domain in domains:
        rule.append(rule_tpl.format(
                domain=domain,
                proxy_name=proxy_name.decode('utf-8')
            )
        )
    surge_conf_content = surge_conf_content.replace('__RULE__',
            "\n".join(rule))
    surge_conf_content = surge_conf_content.replace('__PROXY__',
            surge_proxy)
    return surge_conf_content.encode('utf-8')


def main():
    args = parse_args()
    user_rule = None
    if (args.input):
        with open(args.input, 'rb') as f:
            content = f.read()
    else:
        print 'Downloading gfwlist from %s' % gfwlist_url
        content = urllib2.urlopen(gfwlist_url, timeout=10).read()
    if args.user_rule:
        userrule_parts = urlparse.urlsplit(args.user_rule)
        if not userrule_parts.scheme or not userrule_parts.netloc:
            # It's not an URL, deal it as local file
            with open(args.user_rule, 'rb') as f:
                user_rule = f.read()
        else:
            # Yeah, it's an URL, try to download it
            print 'Downloading user rules file from %s' % args.user_rule
            user_rule = urllib2.urlopen(args.user_rule, timeout=10).read()
    content = decode_gfwlist(content)
    gfwlist = combine_lists(content, user_rule)
    domains = parse_gfwlist(gfwlist)
    domains = reduce_domains(domains)

    surge_conf_content = generate_surge(domains, args.proxy_name, args.surge_proxy)

    loglevel = args.loglevel if args.loglevel else 'notify'
    surge_conf_content = surge_conf_content.replace('__LOGLEVEL__', loglevel)

    all_tcp_mode = args.all_tcp_mode if args.all_tcp_mode == 'true'\
            else 'false'
    surge_conf_content = surge_conf_content.replace('__ALL_TCP_MODE__', all_tcp_mode)

    with open(args.output, 'wb') as f:
        f.write(surge_conf_content)


if __name__ == '__main__':
    main()
