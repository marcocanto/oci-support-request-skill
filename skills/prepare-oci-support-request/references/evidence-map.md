# OCI CLI Evidence Map

Use the service base command plus the issue overlay. All commands are read-only. Exact command availability can differ by OCI CLI version, so validate unfamiliar commands with `--help` before execution.

## Service base commands

| Service key | Primary input | Read-only command |
| --- | --- | --- |
| `block-volume` | `volume_id` | `oci bv volume get --volume-id ...` |
| `compute` | `instance_id` | `oci compute instance get --instance-id ...` |
| `dns` | `zone_name_or_id` | `oci dns zone get --zone-name-or-id ...` |
| `database` | `db_system_id` or `autonomous_database_id` | `oci db system get ...` or `oci db autonomous-database get ...` |
| `postgresql` | `db_system_id` | `oci psql db-system get --db-system-id ...` |
| `fastconnect-vpn` | `virtual_circuit_id` or `ipsec_id` | `oci network virtual-circuit get ...` or `oci network ip-sec-connection get ...` |
| `file-storage` | `file_system_id` or `mount_target_id` | `oci fs file-system get ...` or `oci fs mount-target get ...` |
| `functions` | `function_id` or `application_id` | `oci fn function get ...` or `oci fn application get ...` |
| `identity` | `policy_id` | `oci iam policy get --policy-id ...` |
| `oke` | `cluster_id` or `node_pool_id` | `oci ce cluster get ...` or `oci ce node-pool get ...` |
| `load-balancer` | `load_balancer_id` | Load balancer configuration and aggregate health |
| `network-load-balancer` | `network_load_balancer_id` | Network load balancer configuration and aggregate health |
| `object-storage` | `namespace` and `bucket_name` | `oci os bucket get ...` |
| `streaming` | `stream_id` | `oci streaming admin stream get --stream-id ...` |
| `vcn` | `vcn_id`, `subnet_id`, or related network OCIDs | VCN, subnet, route table, security list, and NSG GET operations |

Optional identifiers trigger focused secondary checks such as `volume_attachment_id`, `volume_backup_id`, `node_pool_id`, `mount_target_id`, `route_table_id`, `security_list_id`, and `nsg_id`.

## Issue overlays

### Control plane, lifecycle, authorization, and configuration

When `compartment_id`, `start_time`, and `end_time` are available, collect Audit events for the narrow incident window. Keep the interval as small as practical. Do not use `--debug`.

### Performance

Collect Monitoring data only when all of these are supplied:

- `compartment_id`
- `metric_namespace`
- `metric_query`
- `start_time`
- `end_time`

The query must name a specific metric, statistic, interval, and resource dimension. Avoid compartment-wide queries with no resource filter.

### Capacity

Collect limit values only when `compartment_id` and `limit_service_name` are known. Capture the exact capacity error separately because capacity availability and service limits are different conditions.

### Connectivity

Collect both ends of the path where possible. For VCN-related issues, include the source and destination VNIC or subnet, route table, security lists, NSGs, gateway, protocol, and ports. OCI configuration does not replace client-side `curl`, `dig`, `traceroute`, `mtr`, or packet evidence.

### Data recovery

Collect the primary resource plus the specific backup, replica, restore, export, or stream identifier. Do not perform a restore, copy, replay, or failover as a diagnostic action.

## Common minimum

Always retain:

- Tenancy and compartment context
- Region and availability domain
- Affected resource OCIDs
- UTC start and most recent failure
- Exact error and `opc-request-id`
- Expected and observed behavior
- Reproduction and last known success
- Recent changes and actions already tried
- Business impact

These are practical diagnostic fields, not a claim that every field is formally mandatory in the Support portal.
