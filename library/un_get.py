#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: un_get
short_description: Manage packages on unRAID using un-get
'''

from ansible.module_utils.basic import AnsibleModule


def parse_package_name(line):
    """Extract clean package name (e.g. zsh-5.9-x86_64-1.txz → zsh)"""
    line = line.strip()
    if not line or line.startswith("Currently") or line.startswith("---"):
        return None
    if line.endswith('.txz'):
        name = line[:-4]
        parts = name.rsplit('-', 3)
        return parts[0] if len(parts) > 1 else name
    return line.split()[0]


def get_installed_packages(module):
    rc, stdout, _ = module.run_command(['un-get', 'installed'])
    if rc != 0:
        module.fail_json(msg="Failed to list installed packages")

    packages = set()
    for line in stdout.splitlines():
        pkg = parse_package_name(line)
        if pkg:
            packages.add(pkg)
    return packages


def run_unget_command(module, cmd, auto_yes=True):
    """Run un-get command and auto-answer 'y' to confirmation prompts."""
    if auto_yes:
        rc, stdout, stderr = module.run_command(cmd, data='y\n', check_rc=False)
    else:
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    output = (stdout + "\n" + stderr).lower()
    if rc != 0 and not any(x in output for x in ["already installed", "abort", "installed", "removed", "nothing to"]):
        module.fail_json(msg=f"Command failed: {' '.join(cmd)}", stdout=stdout, stderr=stderr)

    return rc, stdout, stderr


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', elements='str', aliases=['package', 'pkg']),
            state=dict(type='str', default='present', choices=['present', 'absent', 'latest']),
            update_cache=dict(type='bool', default=False),
            force=dict(type='bool', default=False),   # for latest_force
        ),
        supports_check_mode=True,
    )

    state = module.params['state']
    names = module.params.get('name') or []
    update_cache = module.params['update_cache']
    force = module.params['force']

    result = dict(changed=False, msg='', stdout='')

    # Update cache
    if update_cache and not module.check_mode:
        _, stdout, _ = run_unget_command(module, ['un-get', 'update'], auto_yes=False)
        result['stdout'] += stdout

    if state == 'present':
        installed_before = get_installed_packages(module)
        to_install = [p for p in names if p not in installed_before]

        if not to_install:
            result['msg'] = f"All requested packages already installed: {', '.join(names)}"
            module.exit_json(**result)

        if module.check_mode:
            result['changed'] = True
            result['msg'] = f"Would install: {', '.join(to_install)}"
            module.exit_json(**result)

        _, stdout, _ = run_unget_command(module, ['un-get', 'install'] + to_install)
        result['stdout'] += stdout
        result['changed'] = True
        result['msg'] = f"Installed: {', '.join(to_install)}"

    elif state == 'absent':
        installed_before = get_installed_packages(module)
        to_remove = [p for p in names if p in installed_before]

        if not to_remove:
            result['msg'] = f"No packages to remove: {', '.join(names)}"
            module.exit_json(**result)

        if module.check_mode:
            result['changed'] = True
            result['msg'] = f"Would remove: {', '.join(to_remove)}"
            module.exit_json(**result)

        _, stdout, _ = run_unget_command(module, ['un-get', 'remove'] + to_remove)
        result['stdout'] += stdout
        result['changed'] = True
        result['msg'] = f"Removed: {', '.join(to_remove)}"

    elif state == 'latest':
        cmd = ['un-get', 'upgrade']
        if force:
            cmd.append('--force')

        if module.check_mode:
            result['changed'] = True
            result['msg'] = "Would upgrade all packages"
            module.exit_json(**result)

        _, stdout, _ = run_unget_command(module, cmd)
        result['stdout'] += stdout
        result['changed'] = 'nothing to upgrade' not in stdout.lower()
        result['msg'] = "All packages upgraded" if result['changed'] else "All packages already up to date"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
