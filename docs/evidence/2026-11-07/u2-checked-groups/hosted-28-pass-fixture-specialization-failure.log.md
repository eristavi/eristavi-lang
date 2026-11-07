````text
﻿2026-11-07T06:56:51.4141828Z Current runner version: '2.338.2'
2026-11-07T06:56:51.4161941Z ##[group]Runner Image Provisioner
2026-11-07T06:56:51.4162511Z Hosted Compute Agent
2026-11-07T06:56:51.4162978Z Version: 20261028.624
2026-11-07T06:56:51.4163371Z Commit: 54898b74c23fde5556c9b3c3a2290865feef0dfe
2026-11-07T06:56:51.4163902Z Build Date: 2026-10-28T21:51:42Z
2026-11-07T06:56:51.4164335Z Worker ID: {fe162186-1bb3-413e-8869-bbee436753e4}
2026-11-07T06:56:51.4164765Z Region: centralus
2026-11-07T06:56:51.4165143Z Cloud: Azure
2026-11-07T06:56:51.4165482Z ##[endgroup]
2026-11-07T06:56:51.4166486Z ##[group]Operating System
2026-11-07T06:56:51.4166930Z Ubuntu
2026-11-07T06:56:51.4167261Z 24.04.5
2026-11-07T06:56:51.4167649Z LTS
2026-11-07T06:56:51.4167989Z ##[endgroup]
2026-11-07T06:56:51.4168352Z ##[group]Runner Image
2026-11-07T06:56:51.4168765Z Image: ubuntu-24.04
2026-11-07T06:56:51.4169123Z Version: 20261101.360.1
2026-11-07T06:56:51.4170484Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md
2026-11-07T06:56:51.4171424Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261101.360
2026-11-07T06:56:51.4172041Z ##[endgroup]
2026-11-07T06:56:51.4172728Z ##[group]GITHUB_TOKEN Permissions
2026-11-07T06:56:51.4174317Z Contents: read
2026-11-07T06:56:51.4174711Z Metadata: read
2026-11-07T06:56:51.4175094Z ##[endgroup]
2026-11-07T06:56:51.4176503Z Secret source: Actions
2026-11-07T06:56:51.4177114Z Cache mode: write
2026-11-07T06:56:51.4177716Z Prepare workflow directory
2026-11-07T06:56:51.5137817Z Prepare all required actions
2026-11-07T06:56:51.5181424Z Getting action download info
2026-11-07T06:56:51.7334150Z Download action repository 'actions/checkout@v6' (SHA:d23441a48e516b6c34aea4fa41551a30e30af803)
2026-11-07T06:56:51.8333267Z Download action repository 'actions/setup-python@v6' (SHA:ece7cb06caefa5fff74198d8649806c4678c61a1)
2026-11-07T06:56:51.9165833Z Download action repository 'actions/upload-artifact@v6' (SHA:b7c566a772e6b6bfb58ed0dc250532a479d7789f)
2026-11-07T06:56:52.1692042Z Complete job name: managed-function
2026-11-07T06:56:52.2884517Z ##[group]Run actions/checkout@v6
2026-11-07T06:56:52.2884932Z with:
2026-11-07T06:56:52.2885170Z   repository: eristavi/eristavi-lang
2026-11-07T06:56:52.2887392Z   token: ***
2026-11-07T06:56:52.2887614Z   ssh-strict: true
2026-11-07T06:56:52.2887845Z   ssh-user: git
2026-11-07T06:56:52.2888081Z   persist-credentials: true
2026-11-07T06:56:52.2888338Z   clean: true
2026-11-07T06:56:52.2888572Z   sparse-checkout-cone-mode: true
2026-11-07T06:56:52.2888844Z   fetch-depth: 1
2026-11-07T06:56:52.2889069Z   fetch-tags: false
2026-11-07T06:56:52.2889301Z   show-progress: true
2026-11-07T06:56:52.2889656Z   lfs: false
2026-11-07T06:56:52.2889874Z   submodules: false
2026-11-07T06:56:52.2890113Z   set-safe-directory: true
2026-11-07T06:56:52.2890379Z   allow-unsafe-pr-checkout: false
2026-11-07T06:56:52.2890726Z env:
2026-11-07T06:56:52.2890934Z   CC: clang
2026-11-07T06:56:52.2891167Z   CFLAGS: -O2
2026-11-07T06:56:52.2891412Z ##[endgroup]
2026-11-07T06:56:52.5176669Z Syncing repository: eristavi/eristavi-lang
2026-11-07T06:56:52.5178279Z ##[group]Getting Git version info
2026-11-07T06:56:52.5178963Z Working directory is '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T06:56:52.5179849Z [command]/usr/bin/git version
2026-11-07T06:56:52.5262456Z git version 2.56.0
2026-11-07T06:56:52.5278261Z ##[endgroup]
2026-11-07T06:56:52.5289665Z Temporarily overriding HOME='/home/runner/work/_temp/1f10472f-c11e-4d07-9e74-f6313467b9b2' before making global git config changes
2026-11-07T06:56:52.5291072Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T06:56:52.5293518Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T06:56:52.5348701Z Deleting the contents of '/home/runner/work/eristavi-lang/eristavi-lang'
2026-11-07T06:56:52.5421898Z ##[group]Determining repository object format
2026-11-07T06:56:52.5430401Z ##[endgroup]
2026-11-07T06:56:52.5431026Z ##[group]Initializing the repository
2026-11-07T06:56:52.5431688Z [command]/usr/bin/git init /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T06:56:52.5456953Z hint: Using 'master' as the name for the initial branch. This default branch name
2026-11-07T06:56:52.5457980Z hint: will change to "main" in Git 3.0. To configure the initial branch name
2026-11-07T06:56:52.5458913Z hint: to use in all of your new repositories, which will suppress this warning,
2026-11-07T06:56:52.5459739Z hint: call:
2026-11-07T06:56:52.5460173Z hint:
2026-11-07T06:56:52.5460728Z hint: 	git config --global init.defaultBranch <name>
2026-11-07T06:56:52.5461380Z hint:
2026-11-07T06:56:52.5461979Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
2026-11-07T06:56:52.5462848Z hint: 'development'. The just-created branch can be renamed via this command:
2026-11-07T06:56:52.5463560Z hint:
2026-11-07T06:56:52.5464023Z hint: 	git branch -m <name>
2026-11-07T06:56:52.5464547Z hint:
2026-11-07T06:56:52.5465202Z hint: Disable this message with "git config set advice.defaultBranchName false"
2026-11-07T06:56:52.5467797Z Initialized empty Git repository in /home/runner/work/eristavi-lang/eristavi-lang/.git/
2026-11-07T06:56:52.5477246Z [command]/usr/bin/git remote add origin https://github.com/eristavi/eristavi-lang
2026-11-07T06:56:52.5521668Z ##[endgroup]
2026-11-07T06:56:52.5522419Z ##[group]Disabling automatic garbage collection
2026-11-07T06:56:52.5523814Z [command]/usr/bin/git config --local gc.auto 0
2026-11-07T06:56:52.5551433Z ##[endgroup]
2026-11-07T06:56:52.5552350Z ##[group]Setting up auth
2026-11-07T06:56:52.5552962Z Removing SSH command configuration
2026-11-07T06:56:52.5556391Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T06:56:52.5589023Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T06:56:52.5926554Z Removing HTTP extra header
2026-11-07T06:56:52.5932227Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T06:56:52.5968381Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T06:56:52.6152541Z Removing includeIf entries pointing to credentials config files
2026-11-07T06:56:52.6157313Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T06:56:52.6192700Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T06:56:52.6379318Z [command]/usr/bin/git config --file /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config http.https://github.com/.extraheader AUTHORIZATION: basic ***
2026-11-07T06:56:52.6419652Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T06:56:52.6455305Z [command]/usr/bin/git config --local includeIf.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T06:56:52.6490987Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T06:56:52.6533982Z [command]/usr/bin/git config --local includeIf.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T06:56:52.6567279Z ##[endgroup]
2026-11-07T06:56:52.6567884Z ##[group]Fetching the repository
2026-11-07T06:56:52.6573799Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +6635e8ebff276a82646bd50e936849af54496108:refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.2840143Z From https://github.com/eristavi/eristavi-lang
2026-11-07T06:56:53.2841465Z  * [new ref]         6635e8ebff276a82646bd50e936849af54496108 -> origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.2851144Z [command]/usr/bin/git branch --list --remote origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.2881686Z   origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.2888740Z [command]/usr/bin/git rev-parse refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.2920700Z 6635e8ebff276a82646bd50e936849af54496108
2026-11-07T06:56:53.2943023Z ##[endgroup]
2026-11-07T06:56:53.2943634Z ##[group]Determining the checkout info
2026-11-07T06:56:53.2944344Z ##[endgroup]
2026-11-07T06:56:53.2944755Z [command]/usr/bin/git sparse-checkout disable
2026-11-07T06:56:53.2987843Z [command]/usr/bin/git config --local --unset-all extensions.worktreeConfig
2026-11-07T06:56:53.3020500Z ##[group]Checking out the ref
2026-11-07T06:56:53.3023740Z [command]/usr/bin/git checkout --progress --force -B compiler/u2-cleanup-foundation-20261102 refs/remotes/origin/compiler/u2-cleanup-foundation-20261102
2026-11-07T06:56:53.3627756Z Switched to a new branch 'compiler/u2-cleanup-foundation-20261102'
2026-11-07T06:56:53.3630767Z branch 'compiler/u2-cleanup-foundation-20261102' set up to track 'origin/compiler/u2-cleanup-foundation-20261102'.
2026-11-07T06:56:53.3638738Z ##[endgroup]
2026-11-07T06:56:53.3685177Z [command]/usr/bin/git log -1 --format=%H
2026-11-07T06:56:53.3715256Z 6635e8ebff276a82646bd50e936849af54496108
2026-11-07T06:56:53.4390873Z ##[group]Run actions/setup-python@v6
2026-11-07T06:56:53.4391360Z with:
2026-11-07T06:56:53.4391650Z   python-version: 3.11
2026-11-07T06:56:53.4392009Z   check-latest: false
2026-11-07T06:56:53.4397094Z   token: ***
2026-11-07T06:56:53.4397426Z   update-environment: true
2026-11-07T06:56:53.4397827Z   allow-prereleases: false
2026-11-07T06:56:53.4398213Z   freethreaded: false
2026-11-07T06:56:53.4398542Z env:
2026-11-07T06:56:53.4398806Z   CC: clang
2026-11-07T06:56:53.4399093Z   CFLAGS: -O2
2026-11-07T06:56:53.4399406Z ##[endgroup]
2026-11-07T06:56:53.5285010Z ##[group]Installed versions
2026-11-07T06:56:53.5347170Z Successfully set up CPython (3.11.18)
2026-11-07T06:56:53.5347959Z ##[endgroup]
2026-11-07T06:56:53.6132745Z ##[group]Run python -m pip install -e .
2026-11-07T06:56:53.6133377Z [36;1mpython -m pip install -e .[0m
2026-11-07T06:56:53.6500450Z shell: /usr/bin/bash -e {0}
2026-11-07T06:56:53.6500921Z env:
2026-11-07T06:56:53.6501203Z   CC: clang
2026-11-07T06:56:53.6501476Z   CFLAGS: -O2
2026-11-07T06:56:53.6501900Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:53.6502692Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T06:56:53.6503461Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:53.6504160Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:53.6504840Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:53.6505522Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T06:56:53.6506079Z ##[endgroup]
2026-11-07T06:56:55.9404555Z Obtaining file:///home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T06:56:55.9412737Z   Installing build dependencies: started
2026-11-07T06:56:56.5367939Z   Installing build dependencies: finished with status 'done'
2026-11-07T06:56:56.5372231Z   Checking if build backend supports build_editable: started
2026-11-07T06:56:56.7544534Z   Checking if build backend supports build_editable: finished with status 'done'
2026-11-07T06:56:56.7551423Z   Getting requirements to build editable: started
2026-11-07T06:56:56.9511783Z   Getting requirements to build editable: finished with status 'done'
2026-11-07T06:56:56.9518894Z   Preparing editable metadata (pyproject.toml): started
2026-11-07T06:56:57.0581984Z   Preparing editable metadata (pyproject.toml): finished with status 'done'
2026-11-07T06:56:57.3659179Z Collecting regex==2026.9.29 (from eristavi-lang==0.0.1.dev0)
2026-11-07T06:56:57.4312316Z   Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
2026-11-07T06:56:57.4787914Z Collecting unicodedata2==17.0.0 (from eristavi-lang==0.0.1.dev0)
2026-11-07T06:56:57.4921368Z   Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
2026-11-07T06:56:57.5077985Z Downloading regex-2026.9.29-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (804 kB)
2026-11-07T06:56:57.5498647Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 805.0/805.0 kB 32.2 MB/s  0:00:00
2026-11-07T06:56:57.5644699Z Downloading unicodedata2-17.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (531 kB)
2026-11-07T06:56:57.5699954Z    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 531.5/531.5 kB 93.5 MB/s  0:00:00
2026-11-07T06:56:57.5774299Z Building wheels for collected packages: eristavi-lang
2026-11-07T06:56:57.5780249Z   Building editable for eristavi-lang (pyproject.toml): started
2026-11-07T06:56:57.7174109Z   Building editable for eristavi-lang (pyproject.toml): finished with status 'done'
2026-11-07T06:56:57.7177566Z   Created wheel for eristavi-lang: filename=eristavi_lang-0.0.1.dev0-0.editable-py3-none-any.whl size=4073 sha256=3a869b0e165d12a7d1316b17a94fda022d1c6959d5a78e4bb1da6bc60c7f1a41
2026-11-07T06:56:57.7180457Z   Stored in directory: /tmp/pip-ephem-wheel-cache-ir2qszde/wheels/bf/0e/13/3c92c3d16e7da71040fe0218774d6a7875df473d79c0e7b5aa
2026-11-07T06:56:57.7188865Z Successfully built eristavi-lang
2026-11-07T06:56:57.7293337Z Installing collected packages: unicodedata2, regex, eristavi-lang
2026-11-07T06:56:57.8538539Z
2026-11-07T06:56:57.8544617Z Successfully installed eristavi-lang-0.0.1.dev0 regex-2026.9.29 unicodedata2-17.0.0
2026-11-07T06:56:57.8550628Z
2026-11-07T06:56:57.8550905Z [notice] A new release of pip is available: 26.2.2 -> 26.3
2026-11-07T06:56:57.8551233Z [notice] To update, run: pip install --upgrade pip
2026-11-07T06:56:57.9388700Z ##[group]Run python -m compileall -q tests/test_u2_function_managed_native.py tests/test_u2_function_checked_native.py tests/test_u2_function_checked_group.py compiler
2026-11-07T06:56:57.9389348Z [36;1mpython -m compileall -q tests/test_u2_function_managed_native.py tests/test_u2_function_checked_native.py tests/test_u2_function_checked_group.py compiler[0m
2026-11-07T06:56:57.9407038Z shell: /usr/bin/bash -e {0}
2026-11-07T06:56:57.9407205Z env:
2026-11-07T06:56:57.9407309Z   CC: clang
2026-11-07T06:56:57.9407414Z   CFLAGS: -O2
2026-11-07T06:56:57.9407568Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:57.9407800Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T06:56:57.9408029Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:57.9408248Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:57.9408455Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:57.9408696Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T06:56:57.9408870Z ##[endgroup]
2026-11-07T06:56:58.0612676Z ##[group]Run set -o pipefail
2026-11-07T06:56:58.0612882Z [36;1mset -o pipefail[0m
2026-11-07T06:56:58.0613149Z [36;1mPYTHONPATH=tests python -u -m unittest -v test_u1_words_path 2>&1 | tee "$RUNNER_TEMP/u1a-word-path.log"[0m
2026-11-07T06:56:58.0630604Z shell: /usr/bin/bash -e {0}
2026-11-07T06:56:58.0630739Z env:
2026-11-07T06:56:58.0630843Z   CC: clang
2026-11-07T06:56:58.0630949Z   CFLAGS: -O2
2026-11-07T06:56:58.0631097Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:58.0631331Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T06:56:58.0631559Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:58.0631895Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:58.0632104Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:56:58.0632310Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T06:56:58.0632485Z ##[endgroup]
2026-11-07T06:57:09.6403425Z test_current_radix_paths_and_exact_failure_charges_on_both_runtimes (test_u1_words_path.U1WordPathTests.test_current_radix_paths_and_exact_failure_charges_on_both_runtimes) ... ok
2026-11-07T06:57:09.6404372Z
2026-11-07T06:57:09.6404735Z ----------------------------------------------------------------------
2026-11-07T06:57:09.6405075Z Ran 1 test in 11.255s
2026-11-07T06:57:09.6405207Z
2026-11-07T06:57:09.6405294Z OK
2026-11-07T06:57:09.6631917Z ##[group]Run set -o pipefail
2026-11-07T06:57:09.6632109Z [36;1mset -o pipefail[0m
2026-11-07T06:57:09.6632491Z [36;1mPYTHONPATH=tests python -u -m unittest -v test_u2_function_managed_native test_u2_function_checked_native test_u2_function_checked_group 2>&1 | tee "$RUNNER_TEMP/u2-managed-function.log"[0m
2026-11-07T06:57:09.6648381Z shell: /usr/bin/bash -e {0}
2026-11-07T06:57:09.6648512Z env:
2026-11-07T06:57:09.6648613Z   CC: clang
2026-11-07T06:57:09.6648712Z   CFLAGS: -O2
2026-11-07T06:57:09.6648853Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:57:09.6649080Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T06:57:09.6649303Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:57:09.6649645Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:57:09.6649857Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T06:57:09.6650083Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T06:57:09.6650254Z ##[endgroup]
2026-11-07T06:57:23.6077098Z test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
2026-11-07T06:57:27.3174603Z test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
2026-11-07T06:57:44.1785795Z test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
2026-11-07T06:57:47.3938758Z test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
2026-11-07T06:57:50.6163542Z test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
2026-11-07T06:57:53.8907642Z test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
2026-11-07T06:57:57.2516408Z test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok
2026-11-07T06:58:06.3464124Z test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
2026-11-07T06:58:10.2736411Z test_checked_no_value_success_and_typed_failure_have_no_fake_result (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_no_value_success_and_typed_failure_have_no_fake_result) ... ok
2026-11-07T06:58:14.0144785Z test_checked_one_scalar_result_and_failure_use_distinct_outcomes (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_one_scalar_result_and_failure_use_distinct_outcomes) ... ok
2026-11-07T06:58:19.0556508Z test_checked_recursion_retains_complete_ordered_secondary_context (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context) ... ok
2026-11-07T06:58:23.5238281Z test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
2026-11-07T06:58:27.7019433Z test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
2026-11-07T06:58:30.4565878Z test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
2026-11-07T06:59:02.8271975Z test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
2026-11-07T06:59:06.6012926Z test_missing_native_failure_handoff_or_payload_is_a_terminal_defect (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_missing_native_failure_handoff_or_payload_is_a_terminal_defect) ... ok
2026-11-07T07:00:33.2923277Z test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... U2_CHECKED_OWNED_GENERATOR_SECONDS=76.003592241
2026-11-07T07:00:36.9639193Z ok
2026-11-07T07:00:39.9354801Z test_whole_publication_table_refuses_corruption_and_releases_on_refusal (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_whole_publication_table_refuses_corruption_and_releases_on_refusal) ... ok
2026-11-07T07:01:41.0333497Z test_closed_group_refusals_precede_all_assembly (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_closed_group_refusals_precede_all_assembly) ... ok
2026-11-07T07:01:45.4911096Z test_different_member_recovers_failure_into_normal_parent_result (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_different_member_recovers_failure_into_normal_parent_result) ... ok
2026-11-07T07:01:50.0721028Z test_distinct_normal_signatures_and_result_positions (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_distinct_normal_signatures_and_result_positions) ... ok
2026-11-07T07:01:54.7142931Z test_list_value_crosses_mutual_frames_and_preserves_snapshot (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_list_value_crosses_mutual_frames_and_preserves_snapshot) ... ok
2026-11-07T07:01:58.7824346Z test_missing_sibling_handoff_roots_are_terminal_defects (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_missing_sibling_handoff_roots_are_terminal_defects) ... ok
2026-11-07T07:02:03.7146945Z test_mutual_checked_frames_gc_and_independent_source_outcomes (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_checked_frames_gc_and_independent_source_outcomes) ... ok
2026-11-07T07:02:08.7885067Z test_mutual_frames_preserve_primary_and_ordered_secondary_context (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_frames_preserve_primary_and_ordered_secondary_context) ... ok
2026-11-07T07:02:12.9933012Z test_mutual_native_frame_stack_bound_and_reclamation (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_native_frame_stack_bound_and_reclamation) ... U2_MUTUAL_STACK=[{"depth": 0, "function_stack_bytes": 592}, {"depth": 1, "function_stack_bytes": 1184}, {"depth": 5, "function_stack_bytes": 3552}, {"depth": 32, "function_stack_bytes": 19536}, {"depth": 64, "function_stack_bytes": 38480}]
2026-11-07T07:02:12.9934618Z ok
2026-11-07T07:03:29.9931306Z test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS=62.882
2026-11-07T07:03:30.9196906Z semantic error at 318:114: no analyzed concrete specialization for function 'checkEdge' with (identity compiler.u1_builder.Function, compiler.u1_builder.BlockId, List of compiler.u1_builder.ValueId)
2026-11-07T07:03:30.9212851Z FAIL
2026-11-07T07:03:39.5219798Z test_preflight_work_and_capacity_refusal_release_owned_plans (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_preflight_work_and_capacity_refusal_release_owned_plans) ... ok
2026-11-07T07:03:43.6305797Z test_two_managed_results_cross_member_handoff (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_two_managed_results_cross_member_handoff) ... ok
2026-11-07T07:03:43.6511626Z
2026-11-07T07:03:43.6512187Z ======================================================================
2026-11-07T07:03:43.6512711Z FAIL: test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group)
2026-11-07T07:03:43.6513144Z ----------------------------------------------------------------------
2026-11-07T07:03:43.6513345Z Traceback (most recent call last):
2026-11-07T07:03:43.6517886Z   File "/home/runner/work/eristavi-lang/eristavi-lang/tests/test_u2_function_checked_group.py", line 338, in test_owned_and_c_generators_agree_on_direct_group
2026-11-07T07:03:43.6518352Z     self.assertEqual(build_native(source,c_generator,folder),0)
2026-11-07T07:03:43.6518544Z AssertionError: 1 != 0
2026-11-07T07:03:43.6518624Z
2026-11-07T07:03:43.6518713Z ----------------------------------------------------------------------
2026-11-07T07:03:43.6518898Z Ran 29 tests in 393.775s
2026-11-07T07:03:43.6518991Z
2026-11-07T07:03:43.6519045Z FAILED (failures=1)
2026-11-07T07:03:43.8268045Z ##[error]Process completed with exit code 1.
2026-11-07T07:03:43.8441233Z ##[group]Run actions/upload-artifact@v6
2026-11-07T07:03:43.8441405Z with:
2026-11-07T07:03:43.8441520Z   name: u2-managed-function-1
2026-11-07T07:03:43.8441649Z   retention-days: 14
2026-11-07T07:03:43.8441875Z   path: /home/runner/work/_temp/u2-managed-function.log
/home/runner/work/_temp/u1a-word-path.log

2026-11-07T07:03:43.8442120Z   if-no-files-found: warn
2026-11-07T07:03:43.8442243Z   compression-level: 6
2026-11-07T07:03:43.8442358Z   overwrite: false
2026-11-07T07:03:43.8442473Z   include-hidden-files: false
2026-11-07T07:03:43.8442595Z env:
2026-11-07T07:03:43.8442692Z   CC: clang
2026-11-07T07:03:43.8442794Z   CFLAGS: -O2
2026-11-07T07:03:43.8442936Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:03:43.8443158Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib/pkgconfig
2026-11-07T07:03:43.8443377Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:03:43.8443594Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:03:43.8443795Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.18/x64
2026-11-07T07:03:43.8443997Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.18/x64/lib
2026-11-07T07:03:43.8444164Z ##[endgroup]
2026-11-07T07:03:43.9544034Z Multiple search paths detected. Calculating the least common ancestor of all paths
2026-11-07T07:03:43.9544884Z The least common ancestor is /home/runner/work/_temp. This will be the root directory of the artifact
2026-11-07T07:03:43.9545225Z With the provided path, there will be 2 files uploaded
2026-11-07T07:03:43.9545620Z Artifact name is valid!
2026-11-07T07:03:43.9546072Z Root directory input is valid!
2026-11-07T07:03:44.2459012Z Beginning upload of artifact content to blob storage
2026-11-07T07:03:44.4364809Z Uploaded bytes 1842
2026-11-07T07:03:44.4791795Z Finished uploading artifact content to blob storage!
2026-11-07T07:03:44.4792360Z SHA256 digest of uploaded artifact zip is 9290953588d63752a4a75001b3508f4abc045588e0ec301f2c00eecd26796b4a
2026-11-07T07:03:44.4793779Z Finalizing artifact upload
2026-11-07T07:03:45.0188699Z Artifact u2-managed-function-1.zip successfully finalized. Artifact ID 13565112249
2026-11-07T07:03:45.0190081Z Artifact u2-managed-function-1 has been successfully uploaded! Final size is 1842 bytes. Artifact ID is 13565112249
2026-11-07T07:03:45.0192297Z Artifact download URL: https://github.com/eristavi/eristavi-lang/actions/runs/42349153243/artifacts/13565112249
2026-11-07T07:03:45.0551623Z Post job cleanup.
2026-11-07T07:03:45.1120101Z [command]/usr/bin/git version
2026-11-07T07:03:45.1147279Z git version 2.56.0
2026-11-07T07:03:45.1175424Z Temporarily overriding HOME='/home/runner/work/_temp/045f5dda-c549-4853-b083-3bbf25a1164b' before making global git config changes
2026-11-07T07:03:45.1176242Z Adding repository directory to the temporary git global config as a safe directory
2026-11-07T07:03:45.1179457Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/eristavi-lang/eristavi-lang
2026-11-07T07:03:45.1211785Z Removing SSH command configuration
2026-11-07T07:03:45.1216920Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
2026-11-07T07:03:45.1250716Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
2026-11-07T07:03:45.1469341Z Removing HTTP extra header
2026-11-07T07:03:45.1475615Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
2026-11-07T07:03:45.1509309Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
2026-11-07T07:03:45.1718516Z Removing includeIf entries pointing to credentials config files
2026-11-07T07:03:45.1726648Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
2026-11-07T07:03:45.1766873Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:03:45.1767430Z includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:03:45.1767752Z includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:03:45.1768037Z includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:03:45.1775974Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path
2026-11-07T07:03:45.1805250Z /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.1813859Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git.path /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.1854087Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path
2026-11-07T07:03:45.1882719Z /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.1890161Z [command]/usr/bin/git config --local --unset includeif.gitdir:/home/runner/work/eristavi-lang/eristavi-lang/.git/worktrees/*.path /home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.1928021Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git.path
2026-11-07T07:03:45.1956093Z /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.1963399Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git.path /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.2000336Z [command]/usr/bin/git config --local --get-all includeif.gitdir:/github/workspace/.git/worktrees/*.path
2026-11-07T07:03:45.2027641Z /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.2034122Z [command]/usr/bin/git config --local --unset includeif.gitdir:/github/workspace/.git/worktrees/*.path /github/runner_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config
2026-11-07T07:03:45.2076769Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
2026-11-07T07:03:45.2268921Z Removing credentials config '/home/runner/work/_temp/git-credentials-c02b81af-c188-41b6-84dc-9c69eab18429.config'
2026-11-07T07:03:45.2415409Z Cleaning up orphan processes

````
