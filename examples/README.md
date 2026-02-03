# RouteGuard Examples

Example ClaimRecords, UpdateEvents, and decay cycles.

## Test good output

```bash
python -m routeguard.cli \
  --policy policy.json \
  --file model_output_good.txt
```

Expected:

```
ALLOW: Output passed RouteGuard policy.
```
