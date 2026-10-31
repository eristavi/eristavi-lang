# Owned-runtime investigation: raw evidence and diagnostic harness

31 October 2026. This is documentation, not an installable runtime patch.
External `ptrace` test in `sample.c` was rejected with `Operation not permitted`;
it was not used for measured sampling. `stat_profile.s` supplies the working
in-process SIGPROF sampler. Runtime counters and mapping telemetry were separate
from uninstrumented execution comparisons.

Reproduce from baseline commit `0a2caea09ae9bb05a062a986a3412bc045bbf96b`.
The scripts below are recovered to a disposable directory, with `CHECKOUT_PATH`
and `PROFILE_PATH` replaced by actual absolute paths. Set `PYTHONPATH` to the
checkout and its `tests` directory. Do not apply prototype assembly edits to the
production repository. The embedded scripts otherwise retain the measured logic;
original (pre-path-normalization) SHA-256 is recorded for each.

Sequence:

1. `build_profile.py`; `bench.py` for original C/owned workers.
2. `make_sample.py`; `diagnose.py sample 0`; `remap_samples.py`.
3. `make_counters.py`; `diagnose.py counter 0`.
4. `make_variants.py`; `bench.py filter,filter_lazy,gc4,gc16,combined 0`.
5. `build_verifier.py`; run the six original/combined verifier programs through
   `bench_extra.py`, retaining `*.expected` oracles.
6. `make_cache.py`; run `owned_cache 0`, `combined_cache 0`, and the two
   `*-combined_cache` verifier programs with `bench_extra.py`.
7. `make_memory_probe.py`; run the two memory probes and decode five little-endian
   u64 values: live-at-exit, peak mapped bytes, traffic, reservations, releases.
8. `bench.py combined_cache` for all eight workers; then five serialized
   `bench_extra.py owned 0` / `bench_extra.py combined_cache 0` pairs in AB/BA order.
9. `c_stats.py`; `make_combined_counters.py`; `diagnose.py counter-combined 0`.

No full test matrix or experimental owned compiler self-build is needed to
reproduce these focused observations. Every native result is checked against
its original independent expected output. Original 120-second wall watchdogs
are retained; standalone memory telemetry uses the same bound.

## Raw observations

```json
{
  "baseline_build": {
    "base": "0a2caea09ae9bb05a062a986a3412bc045bbf96b",
    "source_sha256": "73b34a50c300a07b4915b56be38a2867701aeda59c019d9e325c00c247e7c499",
    "assembly_sha256": "12690553f273bb0fdaeff8e2c7010cf6c6cb4483da6b12fc77c053cb9152b8a8",
    "runtime_sha256": "ec6e19184a65c989cbfed2928846ffb01bdd2202be96b54aca899d5ea6409b70",
    "workers": 8,
    "compiler": "gcc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0"
  },
  "platform": "Linux-6.18.57-x86_64-with-glibc2.39",
  "compiler": "gcc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0",
  "cpu_reported": "Intel Xeon Platinum 8573C, KVM virtualized host; hosted CI hardware not matched",
  "sampler": {
    "samples": 6659,
    "functions": [
      [
        "erist_rt_graph_owner",
        1603,
        24.07
      ],
      [
        ".Lg_index_sift",
        1365,
        20.5
      ],
      [
        "erist_rt_graph_mark_roots",
        538,
        8.08
      ],
      [
        "erist_rt_graph_prepare_index",
        469,
        7.04
      ],
      [
        ".Lslots_index_insert",
        355,
        5.33
      ],
      [
        "erist_rt_graph_mark_value",
        292,
        4.39
      ],
      [
        "erist_rt_graph_mark_object",
        258,
        3.87
      ],
      [
        "erist_rt_graph_sweep",
        240,
        3.6
      ],
      [
        "erist_rt_memory_load64",
        191,
        2.87
      ],
      [
        "erist_rt_graph_kind",
        150,
        2.25
      ],
      [
        "erist_rt_free",
        127,
        1.91
      ],
      [
        "erist_rt_graph_find",
        117,
        1.76
      ],
      [
        "erist_rt_freelist_take",
        98,
        1.47
      ],
      [
        ".Lslots_prepare_index",
        92,
        1.38
      ],
      [
        "erist_rt_memory_store64",
        89,
        1.34
      ],
      [
        "erist_rt_release",
        71,
        1.07
      ],
      [
        "erist_rt_text_safe_point",
        57,
        0.86
      ],
      [
        "erist_rt_exit",
        47,
        0.71
      ],
      [
        "erist_rt_slots_collect",
        47,
        0.71
      ],
      [
        ".Lg_bucket",
        44,
        0.66
      ],
      [
        ".Lslots_index_contains",
        37,
        0.56
      ],
      [
        "erist_rt_freelist_push",
        32,
        0.48
      ],
      [
        "erist_rt_graph_snapshot",
        25,
        0.38
      ],
      [
        "evn_binary",
        21,
        0.32
      ],
      [
        "evn_scope_leave",
        21,
        0.32
      ],
      [
        "f45",
        20,
        0.3
      ],
      [
        "erist_rt_value_new",
        17,
        0.26
      ],
      [
        "erist_rt_alloc",
        16,
        0.24
      ],
      [
        "evn_copy",
        16,
        0.24
      ],
      [
        "erist_rt_graph_mark_failure",
        15,
        0.23
      ]
    ]
  },
  "baseline_counters": {
    "erist_rt_alloc": 72284485,
    "erist_rt_free": 72284322,
    "erist_rt_freelist_take": 72284485,
    ".Lfreelist_scan": 76361091,
    ".Lfreelist_reuse": 72281390,
    ".Lfreelist_none": 3095,
    ".Lalloc_new_region": 20,
    "erist_rt_value_new": 68089958,
    "evn_scope_enter": 2367466,
    "evn_scope_leave": 2367466,
    "evn_copy": 38942641,
    "evn_member": 9913652,
    "evn_member_ref": 1475756,
    "evn_index": 2600,
    "evn_index_ref": 0,
    "evn_binary": 13584896,
    "erist_rt_text_safe_point": 68089958,
    "erist_rt_text_collect": 150818,
    "erist_rt_slots_collect": 36806,
    ".Lslots_prepare_index": 36806,
    ".Lslots_index_allocate": 36806,
    "erist_rt_graph_new_capacity": 1784454,
    "erist_rt_graph_prepare_index": 150818,
    "erist_rt_graph_owner": 118397346,
    "erist_rt_graph_find": 218064117,
    "erist_rt_graph_sweep": 150818,
    "erist_rt_text_registry_find": 1721172,
    "evn_frame": 128,
    "evn_pop": 128,
    ".Lslots_clear_unwind_roots": 0,
    "erist_rt_reserve": 36827,
    "erist_rt_release": 36806
  },
  "prototype_counters": {
    "erist_rt_alloc": 72284482,
    "erist_rt_free": 72284275,
    "erist_rt_freelist_take": 72284482,
    ".Lfreelist_scan": 76547225,
    ".Lfreelist_reuse": 72281292,
    ".Lfreelist_none": 3190,
    ".Lalloc_new_region": 19,
    "erist_rt_value_new": 68089958,
    "evn_scope_enter": 2367466,
    "evn_scope_leave": 2367466,
    "evn_copy": 38942641,
    "evn_member": 9913652,
    "evn_member_ref": 1475756,
    "evn_index": 2600,
    "evn_index_ref": 0,
    "evn_binary": 13584896,
    "erist_rt_text_safe_point": 68089958,
    "erist_rt_text_collect": 9735,
    "erist_rt_slots_collect": 36806,
    ".Lslots_prepare_index": 36806,
    ".Lslots_index_allocate": 36806,
    "erist_rt_graph_new_capacity": 1784454,
    "erist_rt_graph_prepare_index": 7729,
    "erist_rt_graph_owner": 33116,
    "erist_rt_graph_find": 37209846,
    "erist_rt_graph_sweep": 9735,
    "erist_rt_text_registry_find": 111314,
    "evn_frame": 128,
    "evn_pop": 128,
    ".Lslots_clear_unwind_roots": 0,
    "erist_rt_reserve": 65,
    "erist_rt_release": 44
  },
  "independent_c_gc": {
    "collections": 55,
    "peak_managed_bytes": 8670142,
    "live_managed_bytes": 1103929,
    "reclaimed_blocks": 3602105
  },
  "mapping_telemetry": [
    {
      "variant": "owned",
      "wall_instrumented": 37.774260594000225,
      "mapping_live_exit": 1327104,
      "mapping_peak_bytes": 1458176,
      "mapping_traffic_bytes": 2896707584,
      "reserve_successes": 36827,
      "release_successes": 36806,
      "oracle_matches": true
    },
    {
      "variant": "combined_cache",
      "wall_instrumented": 7.110994319999918,
      "mapping_live_exit": 1392640,
      "mapping_peak_bytes": 1409024,
      "mapping_traffic_bytes": 2162688,
      "reserve_successes": 65,
      "release_successes": 44,
      "oracle_matches": true
    }
  ],
  "full_integer_workers_and_ablation": [
    {
      "variant": "bootstrap",
      "worker": 0,
      "wall": 2.316618546000427,
      "user": 2.273367,
      "system": 0.042416999999999996,
      "max_rss": 17192,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "bootstrap",
      "worker": 1,
      "wall": 2.2172517799999696,
      "user": 2.196543,
      "system": 0.020087,
      "max_rss": 17208,
      "output_sha256": "6102e5194f1343bcc65ff6d1bf84ae9280dc3a5e4f64b9da77f7e4dcc5f2df94",
      "lines": 13
    },
    {
      "variant": "bootstrap",
      "worker": 2,
      "wall": 1.3868195349996313,
      "user": 1.373942,
      "system": 0.01218,
      "max_rss": 17228,
      "output_sha256": "eb80c5e8bee34a1e6d4b98305e462a7a01ba95641ca7c1e8f213aabb56908ed0",
      "lines": 8
    },
    {
      "variant": "bootstrap",
      "worker": 3,
      "wall": 1.9820950100001937,
      "user": 1.977296,
      "system": 0.004101,
      "max_rss": 18120,
      "output_sha256": "c82825bfe7dad7cf24ed5393e585b373e90e106c7a4fb4a311b36dd208b22363",
      "lines": 2
    },
    {
      "variant": "bootstrap",
      "worker": 4,
      "wall": 1.9426911110003857,
      "user": 1.91059,
      "system": 0.030486,
      "max_rss": 18080,
      "output_sha256": "fe29156d75ee7570f277b31bee52b4e4542a461dd30381c6f24ce2879fd3bac5",
      "lines": 2
    },
    {
      "variant": "bootstrap",
      "worker": 5,
      "wall": 1.9212989249999737,
      "user": 1.889755,
      "system": 0.030504,
      "max_rss": 18320,
      "output_sha256": "72d90bf67683796123648bc12fa1c23d23b17146f12610401a1a056b4531cd65",
      "lines": 2
    },
    {
      "variant": "bootstrap",
      "worker": 6,
      "wall": 1.909366635999504,
      "user": 1.8885429999999999,
      "system": 0.020152,
      "max_rss": 18300,
      "output_sha256": "903dff14a9bb5c196f72e2e30b306d6380d8758e9ec45bd2935415411928ad72",
      "lines": 2
    },
    {
      "variant": "bootstrap",
      "worker": 7,
      "wall": 4.098793090999607,
      "user": 4.066434,
      "system": 0.031617,
      "max_rss": 17596,
      "output_sha256": "fa8588b4a4895c7303d66732d3a8a8033175736eac0212e7cb4de2f7b62a1426",
      "lines": 5
    },
    {
      "variant": "owned",
      "worker": 0,
      "wall": 34.02223255099943,
      "user": 32.170047,
      "system": 1.8445399999999998,
      "max_rss": 10496,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "owned",
      "worker": 1,
      "wall": 33.06941327899949,
      "user": 31.43189,
      "system": 1.634696,
      "max_rss": 10496,
      "output_sha256": "6102e5194f1343bcc65ff6d1bf84ae9280dc3a5e4f64b9da77f7e4dcc5f2df94",
      "lines": 13
    },
    {
      "variant": "owned",
      "worker": 2,
      "wall": 19.76271247800014,
      "user": 18.683983,
      "system": 1.076646,
      "max_rss": 10496,
      "output_sha256": "eb80c5e8bee34a1e6d4b98305e462a7a01ba95641ca7c1e8f213aabb56908ed0",
      "lines": 8
    },
    {
      "variant": "owned",
      "worker": 3,
      "wall": 25.448411131000285,
      "user": 23.735634,
      "system": 1.7109679999999998,
      "max_rss": 10496,
      "output_sha256": "c82825bfe7dad7cf24ed5393e585b373e90e106c7a4fb4a311b36dd208b22363",
      "lines": 2
    },
    {
      "variant": "owned",
      "worker": 4,
      "wall": 25.83421995200024,
      "user": 24.066419,
      "system": 1.765419,
      "max_rss": 10496,
      "output_sha256": "fe29156d75ee7570f277b31bee52b4e4542a461dd30381c6f24ce2879fd3bac5",
      "lines": 2
    },
    {
      "variant": "owned",
      "worker": 5,
      "wall": 25.377014914999563,
      "user": 23.714826,
      "system": 1.6609729999999998,
      "max_rss": 10496,
      "output_sha256": "72d90bf67683796123648bc12fa1c23d23b17146f12610401a1a056b4531cd65",
      "lines": 2
    },
    {
      "variant": "owned",
      "worker": 6,
      "wall": 25.60061459999997,
      "user": 24.115546,
      "system": 1.48302,
      "max_rss": 10496,
      "output_sha256": "903dff14a9bb5c196f72e2e30b306d6380d8758e9ec45bd2935415411928ad72",
      "lines": 2
    },
    {
      "variant": "owned",
      "worker": 7,
      "wall": 55.78628599100011,
      "user": 52.493549,
      "system": 3.289105,
      "max_rss": 10496,
      "output_sha256": "fa8588b4a4895c7303d66732d3a8a8033175736eac0212e7cb4de2f7b62a1426",
      "lines": 5
    },
    {
      "variant": "filter",
      "worker": 0,
      "wall": 27.346594194000318,
      "user": 25.565519,
      "system": 1.779226,
      "max_rss": 10368,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "filter_lazy",
      "worker": 0,
      "wall": 27.045429454999976,
      "user": 25.312783,
      "system": 1.7299069999999999,
      "max_rss": 10496,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "gc4",
      "worker": 0,
      "wall": 14.237240036999538,
      "user": 12.699482,
      "system": 1.536352,
      "max_rss": 10496,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "gc16",
      "worker": 0,
      "wall": 9.273031009999613,
      "user": 7.590129,
      "system": 1.682041,
      "max_rss": 10496,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "combined",
      "worker": 0,
      "wall": 8.65720367799986,
      "user": 6.998445,
      "system": 1.6579769999999998,
      "max_rss": 10496,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "combined_cache",
      "worker": 0,
      "wall": 6.5525378359998285,
      "user": 6.547781,
      "system": 0.0038829999999999997,
      "max_rss": 10368,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e",
      "lines": 15
    },
    {
      "variant": "combined_cache",
      "worker": 1,
      "wall": 6.928080169000168,
      "user": 6.927326,
      "system": 0.0,
      "max_rss": 10496,
      "output_sha256": "6102e5194f1343bcc65ff6d1bf84ae9280dc3a5e4f64b9da77f7e4dcc5f2df94",
      "lines": 13
    },
    {
      "variant": "combined_cache",
      "worker": 2,
      "wall": 4.028487773000052,
      "user": 4.007772,
      "system": 0.015595999999999999,
      "max_rss": 10496,
      "output_sha256": "eb80c5e8bee34a1e6d4b98305e462a7a01ba95641ca7c1e8f213aabb56908ed0",
      "lines": 8
    },
    {
      "variant": "combined_cache",
      "worker": 3,
      "wall": 5.873685325999759,
      "user": 5.850962,
      "system": 0.015547,
      "max_rss": 10496,
      "output_sha256": "c82825bfe7dad7cf24ed5393e585b373e90e106c7a4fb4a311b36dd208b22363",
      "lines": 2
    },
    {
      "variant": "combined_cache",
      "worker": 4,
      "wall": 6.831348783000067,
      "user": 6.809446,
      "system": 0.016988,
      "max_rss": 10496,
      "output_sha256": "fe29156d75ee7570f277b31bee52b4e4542a461dd30381c6f24ce2879fd3bac5",
      "lines": 2
    },
    {
      "variant": "combined_cache",
      "worker": 5,
      "wall": 6.764176441000018,
      "user": 6.734674,
      "system": 0.025155999999999998,
      "max_rss": 10496,
      "output_sha256": "72d90bf67683796123648bc12fa1c23d23b17146f12610401a1a056b4531cd65",
      "lines": 2
    },
    {
      "variant": "combined_cache",
      "worker": 6,
      "wall": 5.871837714999856,
      "user": 5.8440069999999995,
      "system": 0.02643,
      "max_rss": 10496,
      "output_sha256": "903dff14a9bb5c196f72e2e30b306d6380d8758e9ec45bd2935415411928ad72",
      "lines": 2
    },
    {
      "variant": "combined_cache",
      "worker": 7,
      "wall": 14.484850508999443,
      "user": 14.460686,
      "system": 0.016745,
      "max_rss": 10496,
      "output_sha256": "fa8588b4a4895c7303d66732d3a8a8033175736eac0212e7cb4de2f7b62a1426",
      "lines": 5
    }
  ],
  "verifier_and_repeats": [
    {
      "variant": "graphs-bootstrap",
      "worker": null,
      "wall": 3.3184933209995506,
      "user": 3.28287,
      "system": 0.031848999999999995,
      "wait4_maxrss_kib": 17088,
      "sampled_maxrss_kib": 300,
      "output_sha256": "01e6b5fbf11528fdec1a5dd3ad076ccfccb78cabd1beef84201d40e80198e04b"
    },
    {
      "variant": "graphs-owned",
      "worker": null,
      "wall": 80.7999618290005,
      "user": 73.869432,
      "system": 6.922251,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "01e6b5fbf11528fdec1a5dd3ad076ccfccb78cabd1beef84201d40e80198e04b"
    },
    {
      "variant": "graphs-combined",
      "worker": null,
      "wall": 18.984004887999617,
      "user": 12.134733,
      "system": 6.842933,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "01e6b5fbf11528fdec1a5dd3ad076ccfccb78cabd1beef84201d40e80198e04b"
    },
    {
      "variant": "protocol-bootstrap",
      "worker": null,
      "wall": 4.420869682000557,
      "user": 4.37302,
      "system": 0.04683,
      "wait4_maxrss_kib": 16956,
      "sampled_maxrss_kib": 0,
      "output_sha256": "a096ac78c4a7cd2cbaa6cf7e74855e0705aef5473e1dfdd8b4f7a615b9484640"
    },
    {
      "variant": "protocol-owned",
      "worker": null,
      "wall": 57.01696219400037,
      "user": 54.854283,
      "system": 2.158148,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "a096ac78c4a7cd2cbaa6cf7e74855e0705aef5473e1dfdd8b4f7a615b9484640"
    },
    {
      "variant": "protocol-combined",
      "worker": null,
      "wall": 13.32915849300025,
      "user": 11.409452,
      "system": 1.9185949999999998,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "a096ac78c4a7cd2cbaa6cf7e74855e0705aef5473e1dfdd8b4f7a615b9484640"
    },
    {
      "variant": "owned_cache",
      "worker": "0",
      "wall": 33.68764479500078,
      "user": 33.683842,
      "system": 0.0,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.7537841959992875,
      "user": 6.748649,
      "system": 0.0039109999999999995,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "graphs-combined_cache",
      "worker": null,
      "wall": 11.040893664000578,
      "user": 11.035348,
      "system": 0.00402,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "01e6b5fbf11528fdec1a5dd3ad076ccfccb78cabd1beef84201d40e80198e04b"
    },
    {
      "variant": "protocol-combined_cache",
      "worker": null,
      "wall": 11.016440335999505,
      "user": 11.001026,
      "system": 0.012119,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "a096ac78c4a7cd2cbaa6cf7e74855e0705aef5473e1dfdd8b4f7a615b9484640"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 37.39473841199924,
      "user": 35.059195,
      "system": 2.3303599999999998,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.9428700680000475,
      "user": 6.936194,
      "system": 0.004066,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.796282741999676,
      "user": 6.795024,
      "system": 0.0,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 38.92424221100009,
      "user": 36.789347,
      "system": 2.127987,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 35.99606419199972,
      "user": 34.168606,
      "system": 1.822696,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.549618032999206,
      "user": 6.548093,
      "system": 0.0,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 7.123943650000001,
      "user": 7.113895,
      "system": 0.008465,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 39.640468679999685,
      "user": 37.619175,
      "system": 2.013621,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 37.61671536999984,
      "user": 35.395052,
      "system": 2.214278,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 7.840835035000055,
      "user": 7.822213,
      "system": 0.013221,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    }
  ],
  "paired_baseline": [
    {
      "variant": "owned",
      "worker": "0",
      "wall": 37.39473841199924,
      "user": 35.059195,
      "system": 2.3303599999999998,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 38.92424221100009,
      "user": 36.789347,
      "system": 2.127987,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 35.99606419199972,
      "user": 34.168606,
      "system": 1.822696,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 39.640468679999685,
      "user": 37.619175,
      "system": 2.013621,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "owned",
      "worker": "0",
      "wall": 37.61671536999984,
      "user": 35.395052,
      "system": 2.214278,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    }
  ],
  "paired_prototype": [
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.9428700680000475,
      "user": 6.936194,
      "system": 0.004066,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.796282741999676,
      "user": 6.795024,
      "system": 0.0,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 6.549618032999206,
      "user": 6.548093,
      "system": 0.0,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 7.123943650000001,
      "user": 7.113895,
      "system": 0.008465,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    },
    {
      "variant": "combined_cache",
      "worker": "0",
      "wall": 7.840835035000055,
      "user": 7.822213,
      "system": 0.013221,
      "wait4_maxrss_kib": 10368,
      "sampled_maxrss_kib": 0,
      "output_sha256": "500b6a0b0baa51d7840a139181c102bbb60b742ccbb6648a56b9365279ed3b6e"
    }
  ],
  "pairing": "5 serialized fresh-process pairs, alternating AB/BA; same already-built integer.o; no cache flush; 120 s watchdog per native worker; matched output hashes",
  "rss_caveat": "wait4 includes inherited state; per-PID proc attribution unreliable; RSS fields excluded from conclusions",
  "production_changes": "none; diagnostic runtime assembly copies only",
  "full_ci": "not rerun",
  "src_hashes": {
    "src/runtime/allocator_x86_64.eri": "a871f40af1666439509495f75eb1dee0e3cd8cbd89bb92a69f9510ebb5193d5d",
    "src/runtime/float_decimal_x86_64.eri": "b3ccf7396a521bb6e6edbc3f01fd987e2cd73ea1c7ff0c40edfe308c976dfa66",
    "src/runtime/float_format_x86_64.eri": "49ca2cbefb8c7cc691885779a9f0423d0b5eedb726f69f34f30eea7f04b76313",
    "src/runtime/float_parse_x86_64.eri": "96713eddc56a65f5f250cb41fa7f6e60186dbad63ad40fafff5562f45ad63018",
    "src/runtime/float_x86_64.eri": "e1b73f77ac16ffcc50f19e99364ae8e301c8b84c1c3b477209ffc65a1e5adaa4",
    "src/runtime/graph_failure_x86_64.eri": "4ef0526bf342a4232b9da6f9a2806342708ad8d1130cf32dfd983e4b0cf52df2",
    "src/runtime/graph_heap_x86_64.eri": "efba76505ed4b72f27d181165692f12c6867cffb366e3982bb67e1356666f0e6",
    "src/runtime/graph_values_x86_64.eri": "6d30e0f94706a9b84b8b69785d6ff6d197a9c6df6a5d5e34f237f3e6cd614613",
    "src/runtime/linux_x86_64.eri": "5090ef00393563b2afbdbcd958d80ca0214e5f24d26b25c60ecb9bbdb21fa6c7",
    "src/runtime/resource_x86_64.eri": "b33ec065453dec5593b83bb9fc1c29b83be987b0302a506166f89ad076e6813a",
    "src/runtime/scalar_fault_x86_64.eri": "e4119cb1f2ca9c8e8e4a1410761d594488eaf5270740a406fcbcd37caa164f84",
    "src/runtime/scalar_x86_64.eri": "8cb8fb5cb457ab13f076e7246f8079be0649555b987c6764c195af5d3dc1ceaa",
    "src/runtime/slot_index_x86_64.eri": "b0fad75b6ff03b6b0688b506cf8d76371f6f5d94b86e22a918736043058e2155",
    "src/runtime/text_buffer_x86_64.eri": "463876bddbe74445e76bcb6cdf3d8acbfba2b184a8258e1f8d2053e31e7206c4",
    "src/runtime/text_ops_x86_64.eri": "a660e0d1a261d8d1a9d379b36685d9193d8b2a8cb03d77a6053c8f7d59310ee3",
    "src/runtime/text_pool_x86_64.eri": "45211a4f6ccd8df15f8628bde24cdf4f1ed613a702b6613b3a0961f2eb3ef924",
    "src/runtime/text_registry_x86_64.eri": "b4ba2b9b4d5eb9fd7a538b12400950ba838debb64b359da5985d56aa0a811f2c",
    "src/runtime/unicode_grapheme_x86_64.eri": "5ce30a1b212f9abfe0aa2eb6a4d8b9a93ae4f00b0efd726bcb9f26c4e4d4ad9e",
    "src/runtime/unicode_library_x86_64.eri": "0347e00e2969e6aab5a1fc758d467eea549b8cc417c64a6d1542867b68ec99c0",
    "src/runtime/unicode_nfc_tables_x86_64.eri": "993cfa2bdb5be04267dcc8adaf0fab39fa9ab89988f78d596f11842851d3cbc3",
    "src/runtime/unicode_nfc_x86_64.eri": "d28c65f38745ddd65a4a94d065893e4a98356a551c5c221f094baa6be1d4b472",
    "src/runtime/unicode_tables_x86_64.eri": "433a2d296b8d48a3408d80b115614d718c16e6972a905837ba21c0cfced8d171",
    "src/runtime/value_float_x86_64.eri": "e0bd7e929ac85d11c5ab358da6f117c1336cfc4d832902c3f7eef84041091962",
    "src/runtime/value_output_x86_64.eri": "860a21aa933ac60964dd20c3804df0fec5537b7e27d5b5d53454a83d42acc01d",
    "src/runtime/value_roots_x86_64.eri": "11ccc759c3459b17856980a81c625cdbaad83cd9f3bf6222fbd5d6dca70b2dfa",
    "src/runtime/value_scalar_x86_64.eri": "cd81fc63ccec14e1c0e7f3138ab3707d0a0c14573b975aa176af71cd12516268",
    "src/runtime/value_scope_x86_64.eri": "92519fe4653243901dab8cc8d6e2cd9f5a9ec9eed286281c47ab46c0218dce1b",
    "src/runtime/value_text_x86_64.eri": "9790ce37ed81f4646bc91e06f7b5a65c22eb39842749fab47fad7f6080349f6e",
    "src/runtime/value_view_x86_64.eri": "9e3ffa775edd5c7355e80a5c3407e7a6a987858d16286e8df565e0a90576fd2d"
  }
}
```

## build_profile.py

Original SHA-256: `9e53ef4da1f1b3174d3e478d92463ae15e08be5c90accdc9ac92fed983b20ac0`.

```python
import json,os,sys,subprocess,time,hashlib
from pathlib import Path
ROOT=Path('CHECKOUT_PATH')
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_u1_integer_execution import MIN,MAX,MODES,OVERFLOW,source_for,expected_lines
from u1_native_tools import shared_u1_compilers
OUT=Path('PROFILE_PATH')
(OUT/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True) if not (OUT/'compiler').exists() else None
recipes=[(mode,[(MIN,MIN),(MIN,-1)] if mode in (24,25) else [(MIN,MIN)],False,0) for mode in MODES]
recipes += [(mode,[(-1,3)],False,0) for mode in OVERFLOW+(26,27)]
recipes += [(mode,[(-2,MAX),(MAX,0)],True,2) for mode in (203,220,26,127)]
groups=[(recipes[:13],False),(recipes[13:26],False),(recipes[26:34],False)]
groups += [(recipes[i:i+1],False) for i in range(34,len(recipes))]
groups += [([],True)]
(OUT/'groups.json').write_text(json.dumps(groups))
(OUT/'expected.json').write_text(json.dumps([expected_lines(g,l) for g,l in groups]))
source=OUT/'integer.eri';source.write_text(source_for([],groups=groups))
start=time.monotonic();frontend,generator=shared_u1_compilers();print('tools_built',time.monotonic()-start,flush=True)
emitted=subprocess.run([str(frontend),'emit-asm',str(source),'--source-root',str(OUT),'--target','x86_64-linux'],capture_output=True,text=True,timeout=120,check=True)
assert not emitted.stderr,emitted.stderr
runtime=subprocess.run([str(generator)],capture_output=True,text=True,timeout=60,check=True);assert not runtime.stderr
(OUT/'integer.s').write_text(emitted.stdout);(OUT/'runtime.s').write_text(runtime.stdout)
for name in ('integer','runtime'):
    subprocess.run(['as','--64','-L',str(OUT/(name+'.s')),'-o',str(OUT/(name+'.o'))],check=True,capture_output=True)
subprocess.run(['ld','-nostdlib','-static','-e','_start',str(OUT/'integer.o'),str(OUT/'runtime.o'),'-o',str(OUT/'owned')],check=True,capture_output=True)
subprocess.run(['gcc','-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-DERIST_HEAP_GC_INTERVAL=65536',str(OUT/'integer.s'),str(ROOT/'runtime/native_gc_runtime.c'),'-lm','-o',str(OUT/'bootstrap')],check=True,capture_output=True)
(OUT/'symbols.txt').write_text(subprocess.check_output(['nm','-n','-S',str(OUT/'owned')],text=True))
(OUT/'build.json').write_text(json.dumps({'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assembly_sha256':hashlib.sha256((OUT/'integer.s').read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256((OUT/'runtime.s').read_bytes()).hexdigest(),'workers':len(groups),'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0]},indent=2))
print('native_pair_ready',len(groups),flush=True)
```

## bench.py

Original SHA-256: `8235d486f9114bea40cb0eb665ebe2c1c3e7af7642b59a068be0160d36f17f8c`.

```python
from pathlib import Path
import subprocess,os,sys,json,time,threading,hashlib
OUT=Path('PROFILE_PATH');expected=json.loads((OUT/'expected.json').read_text())
variants=sys.argv[1].split(',') if len(sys.argv)>1 else ['bootstrap','owned']
workers=list(map(int,sys.argv[2].split(','))) if len(sys.argv)>2 else list(range(8))
for variant in variants:
 for worker in workers:
  stdout=OUT/f'{variant}-{worker}.out';stderr=OUT/f'{variant}-{worker}.err'
  started=time.monotonic()
  with stdout.open('wb') as out,stderr.open('wb') as err:
   proc=subprocess.Popen([str(OUT/variant),str(worker)],stdout=out,stderr=err,env={'PATH':'/unavailable','LANG':'C'})
   timer=threading.Timer(120,proc.kill);timer.start()
   try:_,status,usage=os.wait4(proc.pid,0);proc.returncode=os.waitstatus_to_exitcode(status)
   finally:timer.cancel()
  text=stdout.read_text();assert proc.returncode==0,(variant,worker,proc.returncode,text[-600:],stderr.read_text())
  assert text.splitlines()==expected[worker],(variant,worker,'oracle mismatch',text[-600:])
  assert not stderr.read_bytes(),stderr.read_text()
  r={'variant':variant,'worker':worker,'wall':time.monotonic()-started,'user':usage.ru_utime,'system':usage.ru_stime,'max_rss':usage.ru_maxrss,'output_sha256':hashlib.sha256(text.encode()).hexdigest(),'lines':len(expected[worker])}
  with (OUT/'bench.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
  print(json.dumps(r),flush=True)
```

## build_verifier.py

Original SHA-256: `18c65c0b2e286583ce42a8fc96b11c460c422c5ac1c0583d9ecb5819512d5406`.

```python
from pathlib import Path
import sys,subprocess,shutil,json,time
ROOT=Path('CHECKOUT_PATH');sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_u1_verifier import graph_probe,PROTOCOL
from u1_native_tools import shared_u1_compilers
p=Path('PROFILE_PATH');frontend,generator=shared_u1_compilers();shutil.copy2(frontend,p/'frontend')
graph,expected=graph_probe(chain_sizes=(128,));(p/'graphs.eri').write_text(graph);(p/'graphs.expected').write_text(expected)
(p/'protocol.eri').write_text((ROOT/'tests/fixtures/u1_verifier.eri').read_text());(p/'protocol.expected').write_text(PROTOCOL)
for name in ('graphs','protocol'):
 r=subprocess.run([str(p/'frontend'),'emit-asm',str(p/(name+'.eri')),'--source-root',str(p),'--target','x86_64-linux'],capture_output=True,text=True,timeout=120,check=True);assert not r.stderr
 (p/(name+'.s')).write_text(r.stdout)
 subprocess.run(['as','--64','-L',str(p/(name+'.s')),'-o',str(p/(name+'.o'))],check=True,capture_output=True)
 for variant,obj in [('owned','runtime.o'),('combined','combined-runtime.o'),('sample','sample-runtime.o')]:
  subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/(name+'.o')),str(p/obj),'-o',str(p/(name+'-'+variant))],check=True,capture_output=True)
 subprocess.run(['gcc','-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-DERIST_HEAP_GC_INTERVAL=65536',str(p/(name+'.s')),str(ROOT/'runtime/native_gc_runtime.c'),'-lm','-o',str(p/(name+'-bootstrap'))],check=True,capture_output=True)
 print(name,'built',flush=True)
# Function index mapping is available from the public diagnostic Universal IR.
r=subprocess.run([str(p/'frontend'),'uir',str(p/'integer.eri'),'--source-root',str(p)],capture_output=True,text=True,timeout=120,check=True)
(p/'integer.uir.json').write_text(r.stdout)
print('uir map ready',len(r.stdout),flush=True)
```

## bench_extra.py

Original SHA-256: `3ebec3bc2b48751845cbd44f76b2d537db27ac73eecf45acf2d9d72f824da4cc`.

```python
from pathlib import Path
import subprocess,os,sys,json,time,threading,hashlib
p=Path('PROFILE_PATH');variant=sys.argv[1];worker=sys.argv[2] if len(sys.argv)>2 else None
binary=p/variant
if worker is None:expected=(p/(variant.split('-')[0]+'.expected')).read_text()
else:expected='\n'.join(json.loads((p/'expected.json').read_text())[int(worker)])+'\n'
cmd=[str(binary)]+([] if worker is None else [worker]);stdout=p/'extra.out';stderr=p/'extra.err';maxrss=[0]
start=time.monotonic()
with stdout.open('wb') as out,stderr.open('wb') as err:
 proc=subprocess.Popen(cmd,stdout=out,stderr=err,env={'PATH':'/unavailable','LANG':'C'})
 done=threading.Event()
 def monitor():
  while not done.wait(.005):
   try:
    status=Path(f'/proc/{proc.pid}/status').read_text()
    if '\nName:\tpython' in '\n'+status:continue
    for line in status.splitlines():
     if line.startswith('VmRSS:'):maxrss[0]=max(maxrss[0],int(line.split()[1]))
   except (FileNotFoundError,ProcessLookupError):pass
 thread=threading.Thread(target=monitor,daemon=True);thread.start();timer=threading.Timer(120,proc.kill);timer.start()
 try:_,status,usage=os.wait4(proc.pid,0);proc.returncode=os.waitstatus_to_exitcode(status)
 finally:done.set();thread.join();timer.cancel()
text=stdout.read_text();assert proc.returncode==0,(variant,worker,proc.returncode,text[-200:],stderr.read_bytes()[-200:]);assert text==expected,(variant,worker,'output mismatch');assert not stderr.read_bytes()
r={'variant':variant,'worker':worker,'wall':time.monotonic()-start,'user':usage.ru_utime,'system':usage.ru_stime,'wait4_maxrss_kib':usage.ru_maxrss,'sampled_maxrss_kib':maxrss[0],'output_sha256':hashlib.sha256(text.encode()).hexdigest()}
with (p/'extra.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
print(json.dumps(r),flush=True)
```

## stat_profile.s

Original SHA-256: `53357868dcff8c57ed2ecaf8e5a1d7c60b6629654cc614f89899b3152567023b`.

```asm
# Diagnostic-only CPU-time sampling, Linux x86-64. No production edits.
.bss
.p2align 3
.Ldiag_samples:
.zero 2097152
.Ldiag_signal_count:
.quad 0
.data
.p2align 3
.Ldiag_action:
.quad .Ldiag_handler
.quad 0x04000004
.quad .Ldiag_restore
.quad 0
.Ldiag_interval:
.quad 0,5000,0,5000
.Ldiag_zero:
.quad 0,0,0,0
.text
.Ldiag_init:
    movl $13,%eax
    movl $27,%edi
    leaq .Ldiag_action(%rip),%rsi
    xorl %edx,%edx
    movl $8,%r10d
    syscall
    testq %rax,%rax
    jne .Ldiag_fail
    movl $38,%eax
    movl $2,%edi
    leaq .Ldiag_interval(%rip),%rsi
    xorl %edx,%edx
    syscall
    testq %rax,%rax
    jne .Ldiag_fail
    ret
.Ldiag_fail:
    movl $60,%eax
    movl $123,%edi
    syscall
.Ldiag_handler:
    incq .Ldiag_signal_count(%rip)
    movq 168(%rdx),%rax
    subq $0x400000,%rax
    shrq $4,%rax
    cmpq $262144,%rax
    jae .Ldiag_handler_done
    leaq .Ldiag_samples(%rip),%rcx
    incq (%rcx,%rax,8)
.Ldiag_handler_done:
    ret
.Ldiag_restore:
    movl $15,%eax
    syscall
.Ldiag_dump:
    pushq %rdi
    movl $38,%eax
    movl $2,%edi
    leaq .Ldiag_zero(%rip),%rsi
    xorl %edx,%edx
    syscall
    movl $1,%eax
    movl $2,%edi
    leaq .Ldiag_samples(%rip),%rsi
    movl $2097152,%edx
    syscall
    popq %rdi
    ret
```

## make_sample.py

Original SHA-256: `7e489567a798bf761a79f908c6368c49497757f3585baa938ebdca551388cbfa`.

```python
from pathlib import Path
import re,subprocess
p=Path('PROFILE_PATH');s=(p/'runtime.s').read_text()
s,n=re.subn(r'(?m)^_start:\n','_start:\n    call .Ldiag_init\n',s);assert n==1
s,n=re.subn(r'(?m)^erist_rt_exit:\n','erist_rt_exit:\n    call .Ldiag_dump\n',s);assert n==1
s+='\n'+(p/'stat_profile.s').read_text();(p/'sample-runtime.s').write_text(s)
subprocess.run(['as','--64','-L',str(p/'sample-runtime.s'),'-o',str(p/'sample-runtime.o')],check=True,capture_output=True)
subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/'integer.o'),str(p/'sample-runtime.o'),'-o',str(p/'sample-owned')],check=True,capture_output=True)
(p/'sample-symbols.txt').write_text(subprocess.check_output(['nm','-n','-S',str(p/'sample-owned')],text=True))
r=subprocess.run([str(p/'sample-owned'),'bad'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert r.returncode==1,(r.returncode,r.stdout,len(r.stderr));assert len(r.stderr)==2097152,len(r.stderr)
print('embedded sampler initialized and exited correctly')
```

## make_counters.py

Original SHA-256: `f3bec89c5ae60b8a4b04ce08362b129235c6b1224c886790ad61890d670a1da0`.

```python
from pathlib import Path
import subprocess,re,json
p=Path('PROFILE_PATH');s=(p/'runtime.s').read_text()
labels=['erist_rt_alloc','erist_rt_free','erist_rt_freelist_take','.Lfreelist_scan','.Lfreelist_reuse','.Lfreelist_none','.Lalloc_new_region','erist_rt_value_new','evn_scope_enter','evn_scope_leave','evn_copy','evn_member','evn_member_ref','evn_index','evn_index_ref','evn_binary','erist_rt_text_safe_point','erist_rt_text_collect','erist_rt_slots_collect','.Lslots_prepare_index','.Lslots_index_allocate','erist_rt_graph_new_capacity','erist_rt_graph_prepare_index','erist_rt_graph_owner','erist_rt_graph_find','erist_rt_graph_sweep','erist_rt_text_registry_find','evn_frame','evn_pop','.Lslots_clear_unwind_roots','erist_rt_reserve','erist_rt_release']
labels=[label for label in labels if re.search('(?m)^'+re.escape(label)+':$',s)]
for i,label in enumerate(labels):
 s,n=re.subn('(?m)^'+re.escape(label)+':\\n',lambda m: m[0]+f'    pushfq\n    incq .Ldiag_counters+{i*8}(%rip)\n    popfq\n',s);assert n==1,(label,n)
s,n=re.subn(r'(?m)^erist_rt_exit:\n',lambda m: m[0]+'    call .Ldiag_count_dump\n',s);assert n==1
s+=f'''\n.bss\n.p2align 3\n.Ldiag_counters:\n.zero {len(labels)*8}\n.text\n.Ldiag_count_dump:\n    pushq %rdi\n    movl $1,%eax\n    movl $2,%edi\n    leaq .Ldiag_counters(%rip),%rsi\n    movl ${len(labels)*8},%edx\n    syscall\n    popq %rdi\n    ret\n'''
(p/'counter-labels.json').write_text(json.dumps(labels));(p/'counter-runtime.s').write_text(s)
subprocess.run(['as','--64','-L',str(p/'counter-runtime.s'),'-o',str(p/'counter-runtime.o')],check=True,capture_output=True)
subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/'integer.o'),str(p/'counter-runtime.o'),'-o',str(p/'counter-owned')],check=True,capture_output=True)
print('counters ready',len(labels))
```

## make_combined_counters.py

Original SHA-256: `e7b3aaf0deaecb3268505ea6e75fd45f8590c99609e9a5a8b13466d16577b9ae`.

```python
from pathlib import Path
import subprocess,re,json
p=Path('PROFILE_PATH');s=(p/'combined_cache-runtime.s').read_text()
labels=['erist_rt_alloc','erist_rt_free','erist_rt_freelist_take','.Lfreelist_scan','.Lfreelist_reuse','.Lfreelist_none','.Lalloc_new_region','erist_rt_value_new','evn_scope_enter','evn_scope_leave','evn_copy','evn_member','evn_member_ref','evn_index','evn_index_ref','evn_binary','erist_rt_text_safe_point','erist_rt_text_collect','erist_rt_slots_collect','.Lslots_prepare_index','.Lslots_index_allocate','erist_rt_graph_new_capacity','erist_rt_graph_prepare_index','erist_rt_graph_owner','erist_rt_graph_find','erist_rt_graph_sweep','erist_rt_text_registry_find','evn_frame','evn_pop','.Lslots_clear_unwind_roots','erist_rt_reserve','erist_rt_release']
labels=[label for label in labels if re.search('(?m)^'+re.escape(label)+':$',s)]
for i,label in enumerate(labels):
 s,n=re.subn('(?m)^'+re.escape(label)+':\\n',lambda m: m[0]+f'    pushfq\n    incq .Ldiag_counters+{i*8}(%rip)\n    popfq\n',s);assert n==1,(label,n)
s,n=re.subn(r'(?m)^erist_rt_exit:\n',lambda m: m[0]+'    call .Ldiag_count_dump\n',s);assert n==1
s+=f'''\n.bss\n.p2align 3\n.Ldiag_counters:\n.zero {len(labels)*8}\n.text\n.Ldiag_count_dump:\n    pushq %rdi\n    movl $1,%eax\n    movl $2,%edi\n    leaq .Ldiag_counters(%rip),%rsi\n    movl ${len(labels)*8},%edx\n    syscall\n    popq %rdi\n    ret\n'''
(p/'counter-labels.json').write_text(json.dumps(labels));(p/'counter-combined-runtime.s').write_text(s)
subprocess.run(['as','--64','-L',str(p/'counter-combined-runtime.s'),'-o',str(p/'counter-combined-runtime.o')],check=True,capture_output=True)
subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/'integer.o'),str(p/'counter-combined-runtime.o'),'-o',str(p/'counter-combined-owned')],check=True,capture_output=True)
print('counters ready',len(labels))
```

## diagnose.py

Original SHA-256: `5946159054b66587b6ad24612cb6f17c53acad19bcdeb01685361beaa276c4e2`.

```python
from pathlib import Path
import subprocess,sys,json,time,struct,bisect,collections
p=Path('PROFILE_PATH');expected=json.loads((p/'expected.json').read_text());kind=sys.argv[1];worker=int(sys.argv[2]);start=time.monotonic()
r=subprocess.run([str(p/(kind+'-owned')),str(worker)],capture_output=True,timeout=120,env={'PATH':'/unavailable','LANG':'C'})
assert r.returncode==0,(r.returncode,r.stdout[-300:],len(r.stderr));assert r.stdout.decode().splitlines()==expected[worker]
(p/f'{kind}-{worker}.bin').write_bytes(r.stderr)
if kind.startswith('counter'):
 labels=json.loads((p/'counter-labels.json').read_text());counts=struct.unpack('<'+'Q'*len(labels),r.stderr);report=dict(zip(labels,counts))
else:
 assert len(r.stderr)==2097152,len(r.stderr)
 symbols=[];locals=[]
 for line in (p/'sample-symbols.txt').read_text().splitlines():
  parts=line.split()
  if len(parts)<3:continue
  address=int(parts[0],16);typ=parts[-2];name=parts[-1]
  if typ.lower()!='t':continue
  locals.append((address,name))
  if not name.startswith('.L'):symbols.append((address,name))
 symbols.sort();locals.sort();addresses=[a for a,n in symbols];localaddresses=[a for a,n in locals]
 functions=collections.Counter();blocks=collections.Counter();counts=struct.unpack('<'+'Q'*262144,r.stderr)
 for i,count in enumerate(counts):
  if not count:continue
  address=0x400000+i*16+8;index=bisect.bisect_right(addresses,address)-1
  if index>=0:functions[symbols[index][1]]+=count
  index=bisect.bisect_right(localaddresses,address)-1
  if index>=0:blocks[locals[index][1]]+=count
 report={'samples':sum(counts),'functions':functions.most_common(25),'blocks':blocks.most_common(30)}
report={'kind':kind,'worker':worker,'wall':time.monotonic()-start,'output_matches':True,'data':report};(p/f'{kind}-{worker}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
```

## remap_samples.py

Original SHA-256: `e17d625e5ee99b1e42280b8e337eaad497bbee7483896676037dde99cbe3a801`.

```python
import re,bisect,collections,struct,json
from pathlib import Path
p=Path('PROFILE_PATH');s=(p/'sample-runtime.s').read_text()+'\n'+(p/'integer.s').read_text()
entries=set(re.findall(r'(?m)^\s*call\s+([.A-Za-z_][\w.]*)',s))
entries|=set(re.findall(r'(?m)^\.globl\s+([.A-Za-z_][\w.]*)',s))
entries|=set(re.findall(r'(?m)^\.type\s+([.A-Za-z_][\w.]*),?\s*@function',s))
symbols=[]
for l in (p/'sample-symbols.txt').read_text().splitlines():
 a=l.split()
 if len(a)>=3 and a[-2].lower()=='t' and a[-1] in entries:symbols.append((int(a[0],16),a[-1]))
symbols.sort();addresses=[x[0] for x in symbols]
counts=struct.unpack('<'+'Q'*262144,(p/'sample-0.bin').read_bytes());c=collections.Counter()
for i,count in enumerate(counts):
 if count:
  at=bisect.bisect_right(addresses,0x400000+i*16+8)-1
  if at>=0:c[symbols[at][1]]+=count
r={'samples':sum(counts),'functions':[(n,x,round(x/sum(counts)*100,2)) for n,x in c.most_common(30)]}
(p/'sample-0-remapped.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
```

## root_filter.s

Original SHA-256: `707931580e85c0e0da53cf5dc3fbd50851e6fb24d1edc2a9c89c35f3c2355f21`.

```asm
# Diagnostic exact-slot membership set. Hash collisions compare exact addresses.
# Same safety rule as independent C runtime: slots already marked separately.
.bss
.p2align 3
.Ldiag_slot_keys:
.zero 1048576
.Ldiag_slot_mask:
.quad 0
.text
.Ldiag_slots_prepare:
    movq $0,.Ldiag_slot_mask(%rip)
    movq .Lvalue_slot_count(%rip),%rax
    cmpq $65528,%rax
    ja .Ldiag_slots_prepared
    leaq 16(%rax,%rax),%rdx
    movl $16,%ecx
.Ldiag_slots_capacity:
    cmpq %rdx,%rcx
    jae .Ldiag_slots_capacity_ready
    addq %rcx,%rcx
    jmp .Ldiag_slots_capacity
.Ldiag_slots_capacity_ready:
    leaq -1(%rcx),%r9
    movq %r9,.Ldiag_slot_mask(%rip)
    leaq .Ldiag_slot_keys(%rip),%rdi
    xorl %eax,%eax
    cld
    rep stosq
    movq .Lvalue_slots(%rip),%r8
    leaq .Ldiag_slot_keys(%rip),%r10
.Ldiag_slots_next:
    testq %r8,%r8
    je .Ldiag_slots_prepared
    movq %r8,%rax
    shrq $4,%rax
    movq %rax,%rcx
    shrq $17,%rcx
    xorq %rcx,%rax
    andq %r9,%rax
.Ldiag_slots_insert:
    cmpq $0,(%r10,%rax,8)
    je .Ldiag_slots_store
    incq %rax
    andq %r9,%rax
    jmp .Ldiag_slots_insert
.Ldiag_slots_store:
    movq %r8,(%r10,%rax,8)
    movq 32(%r8),%r8
    jmp .Ldiag_slots_next
.Ldiag_slots_prepared:
    ret
.Ldiag_slot_contains:
    movq .Ldiag_slot_mask(%rip),%rdx
    testq %rdx,%rdx
    je .Ldiag_slot_absent
    movq %rdi,%rax
    shrq $4,%rax
    movq %rax,%rcx
    shrq $17,%rcx
    xorq %rcx,%rax
    andq %rdx,%rax
    leaq .Ldiag_slot_keys(%rip),%rsi
.Ldiag_slot_find:
    movq (%rsi,%rax,8),%rcx
    testq %rcx,%rcx
    je .Ldiag_slot_absent
    cmpq %rdi,%rcx
    je .Ldiag_slot_present
    incq %rax
    andq %rdx,%rax
    jmp .Ldiag_slot_find
.Ldiag_slot_present:
    movl $1,%eax
    ret
.Ldiag_slot_absent:
    xorl %eax,%eax
    ret
.Ldiag_mark_if_interior:
    subq $8,%rsp
    call .Ldiag_slot_contains
    addq $8,%rsp
    testq %rax,%rax
    je .Lg_mark_interior
    ret
# Before marking starts, determine whether any genuine/non-slot interior root
# requires the interval index. Scratch allocation stays before the marking pass.
.Ldiag_prepare_if_needed:
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    subq $8,%rsp
    cmpq $0,.Ldiag_slot_mask(%rip)
    je .Ldiag_need_index
    movq .Lvalue_scopes(%rip),%r12
.Ldiag_root_frame:
    testq %r12,%r12
    je .Ldiag_root_protected
    movq 16(%r12),%r13
    movq 24(%r12),%r14
    testq %r13,%r13
    je .Ldiag_root_next_frame
    testq %r14,%r14
    je .Ldiag_root_next_frame
    xorl %r15d,%r15d
.Ldiag_root_entry:
    cmpq 32(%r12),%r15
    jae .Ldiag_root_next_frame
    cmpb $1,(%r14,%r15)
    jne .Ldiag_root_next
    movq (%r13,%r15,8),%rdi
    testq %rdi,%rdi
    je .Ldiag_root_next
    call .Ldiag_slot_contains
    testq %rax,%rax
    je .Ldiag_need_index
.Ldiag_root_next:
    incq %r15
    jmp .Ldiag_root_entry
.Ldiag_root_next_frame:
    movq 8(%r12),%r12
    jmp .Ldiag_root_frame
.Ldiag_root_protected:
    movq .Lgraph_protected_value(%rip),%rdi
    testq %rdi,%rdi
    je .Ldiag_no_index
    call .Ldiag_slot_contains
    testq %rax,%rax
    je .Ldiag_need_index
.Ldiag_no_index:
    addq $8,%rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    ret
.Ldiag_need_index:
    call erist_rt_graph_prepare_index
    jmp .Ldiag_no_index
```

## make_variants.py

Original SHA-256: `a1a1b2c504bca4337e9aa1e4b1069c5648333619badc1c1fc98a339a459ca960`.

```python
from pathlib import Path
import subprocess,re,json,hashlib
p=Path('PROFILE_PATH');base=(p/'runtime.s').read_text();helpers=(p/'root_filter.s').read_text()
def build(name,s):
 path=p/(name+'-runtime.s');path.write_text(s)
 subprocess.run(['as','--64','-L',str(path),'-o',str(p/(name+'-runtime.o'))],check=True,capture_output=True)
 subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/'integer.o'),str(p/(name+'-runtime.o')),'-o',str(p/name)],check=True,capture_output=True)
 print(name,hashlib.sha256(s.encode()).hexdigest())
def root_filter(s,lazy=False):
 old='    call erist_rt_graph_prepare_index\n    movq $0,.Lgraph_work(%rip)'
 assert s.count(old)==1
 prefix='    call .Ldiag_slots_prepare\n    call '+('.Ldiag_prepare_if_needed' if lazy else 'erist_rt_graph_prepare_index')+'\n    movq $0,.Lgraph_work(%rip)'
 s=s.replace(old,prefix);assert s.count('call .Lg_mark_interior\n')==2
 s=s.replace('call .Lg_mark_interior\n','call .Ldiag_mark_if_interior\n')
 return s+'\n'+helpers
def frequency(s,factor):
 needle='.Lg_budget_store:\n    movq %rax,.Lgraph_safe_budget(%rip)'
 assert s.count(needle)==1
 return s.replace(needle,'.Lg_budget_store:\n    imulq $'+str(factor)+',%rax\n    movq %rax,.Lgraph_safe_budget(%rip)')
build('filter',root_filter(base));build('filter_lazy',root_filter(base,True))
build('gc4',frequency(base,4));build('gc16',frequency(base,16));build('combined',frequency(root_filter(base,True),16))
```

## scratch_cache.s

Original SHA-256: `71def9efe4b75124c7afc297cc5c5e8b5300f7bbf1766cfc54bd3589cbf6414b`.

```asm
# Diagnostic-only single-owner slot-index scratch cache. No production edits.
.bss
.p2align 3
.Ldiag_scratch_base:
.quad 0
.Ldiag_scratch_length:
.quad 0
.Ldiag_scratch_busy:
.quad 0
.text
.Ldiag_scratch_acquire:
    cmpq $0,.Ldiag_scratch_busy(%rip)
    jne erist_rt_reserve
    movq .Ldiag_scratch_base(%rip),%rax
    testq %rax,%rax
    je .Ldiag_scratch_grow
    cmpq .Ldiag_scratch_length(%rip),%rdi
    ja .Ldiag_scratch_grow
    movq .Ldiag_scratch_length(%rip),%rcx
    movq %rax,%rdi
    shrq $3,%rcx
    xorl %eax,%eax
    cld
    rep stosq
    movq .Ldiag_scratch_base(%rip),%rax
    movq .Ldiag_scratch_length(%rip),%rdx
    movq $1,.Ldiag_scratch_busy(%rip)
    ret
.Ldiag_scratch_grow:
    pushq %r12
    pushq %r13
    subq $8,%rsp
    call erist_rt_reserve
    testq %rax,%rax
    je .Ldiag_scratch_failed
    movq %rax,%r12
    movq %rdx,%r13
    movq .Ldiag_scratch_base(%rip),%rdi
    testq %rdi,%rdi
    je .Ldiag_scratch_install
    movq .Ldiag_scratch_length(%rip),%rsi
    call erist_rt_release
.Ldiag_scratch_install:
    movq %r12,.Ldiag_scratch_base(%rip)
    movq %r13,.Ldiag_scratch_length(%rip)
    movq $1,.Ldiag_scratch_busy(%rip)
    movq %r12,%rax
    movq %r13,%rdx
.Ldiag_scratch_failed:
    addq $8,%rsp
    popq %r13
    popq %r12
    ret
.Ldiag_scratch_release:
    cmpq .Ldiag_scratch_base(%rip),%rdi
    jne erist_rt_release
    movq $0,.Ldiag_scratch_busy(%rip)
    xorl %eax,%eax
    ret
```

## make_cache.py

Original SHA-256: `e17ad22c2cbbad45b2affd87b1b17c56afd134a18b564d4d043cba420e9b0e08`.

```python
from pathlib import Path
import subprocess
p=Path('PROFILE_PATH');helpers=(p/'scratch_cache.s').read_text()
for variant in ('owned','combined'):
 s=(p/('runtime.s' if variant=='owned' else 'combined-runtime.s')).read_text()
 a=s.index('.Lslots_prepare_index:');b=s.index('.Lslots_index_unavailable:',a)
 part=s[a:b];assert part.count('call erist_rt_reserve')==1
 s=s[:a]+part.replace('call erist_rt_reserve','call .Ldiag_scratch_acquire')+s[b:]
 a=s.index('erist_rt_slots_collect:');b=s.index('.size erist_rt_slots_collect',a)
 part=s[a:b];assert part.count('call erist_rt_release')==1
 s=s[:a]+part.replace('call erist_rt_release','call .Ldiag_scratch_release')+s[b:]+helpers
 name=variant+'_cache';(p/(name+'-runtime.s')).write_text(s)
 subprocess.run(['as','--64','-L',str(p/(name+'-runtime.s')),'-o',str(p/(name+'-runtime.o'))],check=True,capture_output=True)
 for workload in ('integer','graphs','protocol'):
  binary=name if workload=='integer' else workload+'-'+name
  subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/(workload+'.o')),str(p/(name+'-runtime.o')),'-o',str(p/binary)],check=True,capture_output=True)
 print(name,'built',flush=True)
```

## make_memory_probe.py

Original SHA-256: `7003854ff4a3617f91253d0b7eaeda71fdada77777c5f95af45cd2eddc2e1789`.

```python
from pathlib import Path
import re,subprocess
p=Path('PROFILE_PATH')
for variant in ('owned','combined_cache'):
 s=(p/('runtime.s' if variant=='owned' else variant+'-runtime.s')).read_text()
 before='    cmpq $-4095,%rax\n    jae .Lreserve_fail\n    ret'
 assert s.count(before)==1
 s=s.replace(before,'''    cmpq $-4095,%rax
    jae .Lreserve_fail
    pushfq
    pushq %rcx
    movq .Ldiag_map_live(%rip),%rcx
    addq %rdx,%rcx
    movq %rcx,.Ldiag_map_live(%rip)
    addq %rdx,.Ldiag_map_traffic(%rip)
    incq .Ldiag_map_count(%rip)
    cmpq .Ldiag_map_peak(%rip),%rcx
    jbe .Ldiag_map_no_peak
    movq %rcx,.Ldiag_map_peak(%rip)
.Ldiag_map_no_peak:
    popq %rcx
    popfq
    ret''')
 before='erist_rt_release:\n    movl $11,%eax\n    syscall\n    ret';assert s.count(before)==1
 s=s.replace(before,'''erist_rt_release:
    movl $11,%eax
    syscall
    pushfq
    testq %rax,%rax
    jne .Ldiag_release_failed
    subq %rsi,.Ldiag_map_live(%rip)
    incq .Ldiag_release_count(%rip)
.Ldiag_release_failed:
    popfq
    ret''')
 s=s.replace('erist_rt_exit:\n','erist_rt_exit:\n    call .Ldiag_memory_dump\n',1)
 s+='''\n.bss
.p2align 3
.Ldiag_map_live: .quad 0
.Ldiag_map_peak: .quad 0
.Ldiag_map_traffic: .quad 0
.Ldiag_map_count: .quad 0
.Ldiag_release_count: .quad 0
.text
.Ldiag_memory_dump:
    pushq %rdi
    movl $1,%eax
    movl $2,%edi
    leaq .Ldiag_map_live(%rip),%rsi
    movl $40,%edx
    syscall
    popq %rdi
    ret
'''
 name='memory-'+variant;(p/(name+'.s')).write_text(s)
 subprocess.run(['as','--64','-L',str(p/(name+'.s')),'-o',str(p/(name+'.o'))],check=True,capture_output=True)
 subprocess.run(['ld','-nostdlib','-static','-e','_start',str(p/'integer.o'),str(p/(name+'.o')),'-o',str(p/name)],check=True,capture_output=True)
print('memory probes built')
```

## c_stats.py

Original SHA-256: `11a29cc48105f65bdbab73a0a7d7c8c4ab72691d22b3c9683726fb924dd8c658`.

```python
from pathlib import Path
import subprocess,json,time
p=Path('PROFILE_PATH');root=Path('CHECKOUT_PATH')
source=p/'c-stats.c';source.write_text('#include "'+str(root/'runtime/native_gc_runtime.c')+'"\n#include <stdio.h>\n__attribute__((destructor)) static void diag_stats(void){fprintf(stderr,"{\\\"collections\\\":%zu,\\\"peak_managed_bytes\\\":%zu,\\\"live_managed_bytes\\\":%zu,\\\"reclaimed_blocks\\\":%zu}\\n",eri_native_heap_collections(),eri_native_heap_peak_bytes(),eri_native_heap_live_bytes(),eri_native_heap_reclaimed_blocks());}\n')
subprocess.run(['gcc','-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-DERIST_HEAP_GC_INTERVAL=65536',str(p/'integer.s'),str(source),'-lm','-o',str(p/'c-stats')],check=True,capture_output=True)
r=subprocess.run([str(p/'c-stats'),'0'],capture_output=True,timeout=120);assert r.returncode==0;assert r.stdout.decode().splitlines()==json.loads((p/'expected.json').read_text())[0]
stats=json.loads(r.stderr);(p/'c-stats.json').write_text(json.dumps(stats,indent=2));print(stats)
```

## sample.c

Original SHA-256: `8d21cd5d2044e1f3db20997532ab921563217145cee5a42854c63d99e7a638d2`.

```c
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <sys/prctl.h>
#include <signal.h>
#include <errno.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <fcntl.h>
int main(int argc,char **argv){
 if(argc<4)return 2;
 pid_t pid=fork();if(pid<0)return 3;
 if(!pid){
  int fd=open(argv[1],O_WRONLY|O_CREAT|O_TRUNC,0600);if(fd<0)_exit(4);dup2(fd,1);close(fd);
  if(ptrace(PTRACE_TRACEME,0,0,0)<0){perror("ptrace");_exit(5);}raise(SIGSTOP);execv(argv[2],argv+2);perror("exec");_exit(6);
 }
 int status;if(waitpid(pid,&status,0)<0)return 7;
 if(!WIFSTOPPED(status))return 8;
 ptrace(PTRACE_SETOPTIONS,pid,0,PTRACE_O_EXITKILL);
 if(ptrace(PTRACE_CONT,pid,0,0)<0)return 9;
 struct timespec pause={0,5000000};unsigned samples=0;
 for(;;){
  nanosleep(&pause,0);
  pid_t got=waitpid(pid,&status,WNOHANG);
  if(got==pid){if(WIFEXITED(status))return WEXITSTATUS(status);if(WIFSIGNALED(status))return 128+WTERMSIG(status);if(WIFSTOPPED(status)){ptrace(PTRACE_CONT,pid,0,0);continue;}}
  if(got<0)return 10;
  if(kill(pid,SIGSTOP)<0){waitpid(pid,&status,0);return WIFEXITED(status)?WEXITSTATUS(status):11;}
  if(waitpid(pid,&status,0)<0)return 12;
  if(WIFEXITED(status))return WEXITSTATUS(status);
  if(WIFSIGNALED(status))return 128+WTERMSIG(status);
  struct user_regs_struct regs;
  if(ptrace(PTRACE_GETREGS,pid,0,&regs)<0)return 13;
  printf("%llx",regs.rip);
  unsigned long frame=regs.rbp;
  for(unsigned depth=0;depth<8 && frame>=regs.rsp && frame-regs.rsp<1048576;depth++){
   errno=0;unsigned long ret=ptrace(PTRACE_PEEKDATA,pid,(void*)(frame+8),0);if(errno)break;
   errno=0;unsigned long next=ptrace(PTRACE_PEEKDATA,pid,(void*)frame,0);if(errno)break;
   printf(" %lx",ret);if(next<=frame||next-frame>1048576)break;frame=next;
  }
  putchar('\n');samples++;
  if(samples>24000){kill(pid,SIGKILL);waitpid(pid,&status,0);return 124;}
  if(ptrace(PTRACE_CONT,pid,0,0)<0)return 14;
 }
}
```
