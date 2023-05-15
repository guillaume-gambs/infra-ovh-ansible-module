#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: dedicated_server_backupftp_acl

short_description: Manage acl for backup storage on dedicated server.

description:
    - This module manage acl on backup storage for a dedicated server.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description:
            - The service_name
    cifs:
        required: false
        default: false
        choices: ['true','false']
        description:
            - Enable/disable cifs on acl
            - Wether to allow the CIFS (SMB) protocol for this ACL
    ftp:
        required: false
        default: false
        choices: ['true','false']
        description:
            - Enable/disable ftp on acl
            - Wether to allow the FTP protocol for this ACL
    nfs:
        required: false
        default: false
        choices: ['true','false']
        description:
            - Enable/disable nfs on acl
            - Wether to allow the NFS protocol for this ACL
    ip:
        required: true
        type: ipBlock
        description:
            - The IP Block specific to this ACL.
            - It musts belong to your server.
    state:
        required: false
        default: present
        choices: ['present','absent']
        description:
            - Indicate the desired state of volume
'''

EXAMPLES = r'''
- name: Manage acl on backup storage of {{ service_name }}
  synthesio.ovh.dedicated_server_backupftp_acl:
    service_name: "{{ service_name }}"
    ftp: false
    nfs: true
    cifs: false
    ip: {{ ip }}
    state: present
  delegate_to: localhost
  register: backup_storage_acl
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    ovh_api_connect,
    ovh_argument_spec,
)
import urllib.parse


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
            cifs=dict(required=False, default=False, type='bool'),
            ftp=dict(required=False, default=False, type='bool'),
            nfs=dict(required=False, default=False, type='bool'),
            ip=dict(required=True),
            state=dict(
                required=False,
                choices=["present", "absent"],
                default="present"),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)

    service_name = module.params["service_name"]
    cifs = module.params["cifs"]
    ftp = module.params["ftp"]
    nfs = module.params["nfs"]
    # url encode the ip mask (/32 -> %2F)
    ip =  module.params["ip"]
    ip_encode = urllib.parse.quote(ip, safe='')
    state = module.params["state"]

    try:
        backup_storage_info_acl = client.get(
            "/dedicated/server/%s/features/backupFTP/access/%s" % (
                service_name,
                ip_encode
            )
        )
        backup_storage_acl_exist = True

    except ResourceNotFoundError:
        backup_storage_acl_exist = False

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if state == "present" and backup_storage_acl_exist:
        if module.check_mode:
            module.exit_json(
                msg="Reapply ACL on backup storage {} on IP {} - (dry run mode)".format(
                    service_name,
                    ip,
                ),
                changed=True,
                **backup_storage_info_acl,
            )

        client.put(
            "/dedicated/server/%s/features/backupFTP/access/%s" % (service_name, ip_encode),
            cifs=cifs,
            ftp=ftp,
            nfs=nfs,
        )

        try:
            backup_storage_apply_acl = client.get(
                "/dedicated/server/%s/features/backupFTP/access/%s" % (service_name, ip_encode)
            )
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error)
            )

        module.exit_json(
            msg="Reapply ACL on backup storage {} on IP {}".format(
                service_name,
                ip,
            ),
            changed=True,
            **backup_storage_apply_acl,
        )

    elif state == "present" and not backup_storage_acl_exist:

        if module.check_mode:
            module.exit_json(
                msg="Create ACL on backup storage {} on IP {} - (dry run mode)".format(
                    service_name,
                    ip,
                ),
                changed=True,
            )

        try:
            result = client.post(
                "/dedicated/server/%s/features/backupFTP/access" % service_name,
                cifs=cifs,
                ftp=ftp,
                nfs=nfs,
                ipBlock=ip,
            )
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error)
            )

        try:
            backup_storage_apply_acl = client.get(
                "/dedicated/server/%s/features/backupFTP/access/%s" % (service_name, ip_encode)
            )
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

        module.exit_json(
            msg="Enable backup storage of {}".format(service_name),
            changed=True,
            **backup_storage_apply_acl,
        )

    elif state == "absent" and backup_storage_acl_exist:

        if module.check_mode:
            module.exit_json(
                msg="Delete ACL on backup storage {} for ip {} - (dry run mode)".format(
                    service_name, ip
                ),
                changed=True,
            )

        try:
            result = client.delete(
                "/dedicated/server/%s/features/backupFTP/access/%s" % (service_name, ip_encode)
            )

            module.exit_json(
                msg="Revoke ACL on backup storage {} for ip {}".format(
                    service_name, ip
                ),
                changed=True,
                **result,
            )

        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error)
            )

    else:  # elif state == "absent" and not backup_storage_acl_exist:
        if module.check_mode:
            module.exit_json(
                msg="ACL of backup storage {} is already revoked for ip {} - (dry run mode)".format(
                    service_name,
                    ip,
                ),
                changed=False,
            )

        module.exit_json(
            msg="ACL of backup storage {} is already revoked for ip {}".format(
                service_name, ip
            ),
            changed=False,
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
