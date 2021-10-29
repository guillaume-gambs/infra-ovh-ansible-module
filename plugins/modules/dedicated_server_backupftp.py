#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: dedicated_server_backupftp

short_description: Manage OVH API for backup storage on dedicated server.

description:
    - This module enable or disable backup storage on dedicated server.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service_name
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of volume
'''

EXAMPLES = r'''
- name: Ensure Backupftp is state wanted
  synthesio.ovh.dedicated_server_backupftp:
    service_name: "{{ service_name }}"
    state: present
  delegate_to: localhost
  register: backup_storage
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError, ResourceNotFoundError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            state=dict(choices=["present", "absent"], default="present"),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)

    service_name = module.params["service_name"]
    state = module.params["state"]

    try:
        backup_storage_info = client.get(
            "/dedicated/server/%s/features/backupFTP" % service_name
        )
        backup_storage = True

    except ResourceNotFoundError:
        backup_storage = False

    if state == "present" and backup_storage:
        if module.check_mode:
            module.exit_json(
                msg="Backup storage of {} is already enable - (dry run mode)".format(
                    service_name
                ),
                changed=False,
                **backup_storage_info
            )

        module.exit_json(
            msg="Backup storage of {} is already enable".format(service_name),
            changed=False,
            **backup_storage_info
        )

    elif state == "present" and not backup_storage:
        if module.check_mode:
            module.exit_json(
                msg="Enable backup storage of {} - (dry run mode)".format(service_name),
                changed=True,
            )

        try:
            result = client.post(
                "/dedicated/server/%s/features/backupFTP" % service_name
            )

            module.exit_json(
                msg="Enable backup storage of {}".format(service_name),
                changed=True,
                **result
            )

        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    elif state == "absent" and backup_storage:
        if module.check_mode:
            module.exit_json(
                msg="Disable backup storage of {} to state {} - (dry run mode)".format(
                    service_name, state
                ),
                changed=True,
            )

        try:
            result = client.delete(
                "/dedicated/server/%s/features/backupFTP" % service_name
            )

            module.exit_json(
                msg="Disable backup storage of {}, all data will be erased".format(
                    service_name
                ),
                changed=True,
                **result
            )

        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    else:  # elif state == "absent" and not backup_storage:
        if module.check_mode:
            module.exit_json(
                msg="Backup storage of {} is already disable - (dry run mode)".format(
                    service_name
                ),
                changed=False,
            )

        module.exit_json(
            msg="Backup storage of {} is already disable".format(service_name),
            changed=False,
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
