# Aqara Agent

Aqara Home **AI Agent skill**: homes, rooms, devices, scenes, automations, and energy statistics through the **Aqara Open API**, with natural language on the agent side and **`scripts/aqara_open_api.py`** on the wire.

**Canonical spec:** [`SKILL.md`](SKILL.md) (workflow, **Must** / **Forbidden**, routing, errors, **Out of Scope**). This file is an index only and does not override it.

## What It Covers

- **Space:** homes, rooms, `home_id` selection, switching home  
- **Devices:** query, status, logs, base info; control via `post_device_control` (bounds: [`assets/device_control_action_table.csv`](assets/device_control_action_table.csv) + [`devices-control.md`](references/devices-control.md))  
- **Scenes:** catalog list, scenes by device, execute, recommend, create, snapshot, detail, execution logs  
- **Automations:** list (catalog + by device), detail, toggle, execution logs  
- **Energy:** consumption / cost-style statistics (device, room, or home)

Example intents: *"How many lights are at home?"*, *"Switch to my other home."*, *"Turn off the living room AC."*, *"Run the Movie scene."*, *"Recommend a bedtime setup for the bedroom."*, *"Capture a scene snapshot."*, *"What automations do I have?"*, *"Check automation execution in the bedroom for the last three days."*

## Repository Layout

| Path | Role |
|------|------|
| [`SKILL.md`](SKILL.md) | Normative instructions for hosts and models |
| [`README.md`](README.md) | This file |
| [`assets/login_reply_prompt.json`](assets/login_reply_prompt.json) | Locales, **`official_open_login_url`**, **`login_url_policy`** |
| [`assets/user_account.example.json`](assets/user_account.example.json) | Template for session JSON |
| [`assets/user_account.json`](assets/user_account.json) | Live credentials + `home_id` / `home_name` (**sensitive**) |
| [`assets/device_control_action_table.csv`](assets/device_control_action_table.csv) | Normative `attribute` / `action` / `value` mapping for control and scene slots |
| [`scripts/aqara_open_api.py`](scripts/aqara_open_api.py) | CLI + `AqaraOpenAPI` client |
| [`scripts/save_user_account.py`](scripts/save_user_account.py) | Persist `aqara_api_key` / home selection |
| [`scripts/runtime_utils.py`](scripts/runtime_utils.py) | Shared helpers |
| [`scripts/requirements.txt`](scripts/requirements.txt) | Python dependencies |

### `references/` (procedures + bash examples)

| Doc | Topic |
|-----|--------|
| [`aqara-account-manage.md`](references/aqara-account-manage.md) | Login, token save, re-auth, logout |
| [`home-space-manage.md`](references/home-space-manage.md) | Homes, rooms, selecting a home |
| [`devices-inquiry.md`](references/devices-inquiry.md) | Lists, status, logs |
| [`devices-control.md`](references/devices-control.md) | Control commands and bounds |
| [`scene-manage.md`](references/scene-manage.md) | Scene **index**; normative splits under [`references/scene-workflow/`](references/scene-workflow/) |
| [`automation-manage.md`](references/automation-manage.md) | Automation **index**; splits under [`references/automation-workflow/`](references/automation-workflow/) |
| [`energy-statistic.md`](references/energy-statistic.md) | Energy / cost stats |
| [`weather-forecast.md`](references/weather-forecast.md) | Outdoor weather API (**only** with scene recommend leaving-home step) |

**Scene workflow files** (enter via [`scene-manage.md`](references/scene-manage.md)): [`list.md`](references/scene-workflow/list.md) (`#catalog-list`, `#scenes-by-device`), [`execute.md`](references/scene-workflow/execute.md), [`recommend.md`](references/scene-workflow/recommend.md), [`create.md`](references/scene-workflow/create.md), [`snapshot.md`](references/scene-workflow/snapshot.md), [`execution-log.md`](references/scene-workflow/execution-log.md), [`failure-response.md`](references/scene-workflow/failure-response.md), [`appendices.md`](references/scene-workflow/appendices.md).

**Automation workflow files** (enter via [`automation-manage.md`](references/automation-manage.md)): [`list.md`](references/automation-workflow/list.md) (`#catalog-list`, `#by-device`), [`toggle.md`](references/automation-workflow/toggle.md), [`execution-log.md`](references/automation-workflow/execution-log.md), [`failure-response.md`](references/automation-workflow/failure-response.md).

## Setup

1. **Python** 3 with `pip`.

2. **Install deps** (run from **this** directory — the folder that contains `scripts/`):

   ```bash
   pip install -r scripts/requirements.txt
   ```

3. **API host** (optional): default is production (`agent.aqara.com`); for test, e.g.:

   ```bash
   export AQARA_OPEN_HOST=agent.aqara.com
   ```

4. **Session file:** start from [`assets/user_account.example.json`](assets/user_account.example.json) -> `assets/user_account.json`, then follow [`references/aqara-account-manage.md`](references/aqara-account-manage.md) for login and [`references/home-space-manage.md`](references/home-space-manage.md) for home selection.

5. **Login URL:** agents **must** show users **exactly** the string in `login_reply_prompt.json` -> **`official_open_login_url`** (read **`login_url_policy`**). **Forbidden** invent Open Platform / `sns-auth` / OAuth-style URLs.

6. **After pasting `aqara_api_key`:** run `save_user_account.py` and **`get_homes`** as **two separate** shell runs (no `&&` chain); see account + home-space references.

## CLI

```bash
python3 scripts/aqara_open_api.py <method_name> [json_body]
```

Use **only** method names that appear on `AqaraOpenAPI` and in the bash examples inside `references/*.md`. `get_*` -> no JSON body; `post_*` -> optional JSON object.

Optional env: `AQARA_OPEN_HTTP_TIMEOUT`, `AQARA_OPEN_API_URL` (see [`SKILL.md`](SKILL.md)).

## 方法名速查

与 [`SKILL.md`](SKILL.md) **Methods (ground list)** 一致，作为 `aqara_open_api.py` 第一个参数的合法方法名；**勿**使用未出现在下列清单（且未在 `references/` 中增补）的名称。

**`get_*`（无 JSON body）**

`get_homes`, `get_rooms`, `get_home_devices`, `get_home_scenes`, `get_home_automations`

**`post_*`（JSON 可选，默认 `{}`）**

`post_current_outdoor_weather`, `post_device_base_info`, `post_device_status`, `post_device_control`, `post_device_log`, `post_execute_scene`, `post_scene_detail_query`, `post_create_scene`, `post_scene_snapshot`, `post_scene_execution_log`, `post_automation_detail_query`, `post_automation_execution_log`, `post_automation_switch`, `post_energy_consumption_statistic`

`post_current_outdoor_weather` **仅**用于场景推荐离家步骤，见 [`weather-forecast.md`](references/weather-forecast.md) / [`recommend.md`](references/scene-workflow/recommend.md)。能耗字段与路由见 [`energy-statistic.md`](references/energy-statistic.md)。

## Security and Sharing

- Treat **`assets/user_account.json`** as secret; do not commit or ship it in public bundles.  
- Distribute **`user_account.example.json`** plus docs; recipients create their own `user_account.json` after login.

## Limitations

Cameras, door-unlock flows, authoring new automations from scratch, shortcuts, general weather Q&A, and entertainment beyond [`devices-control.md`](references/devices-control.md) are out of scope for this wrapper. Outdoor weather fetch (`post_current_outdoor_weather`) is **only** for the **Scene recommend workflow** leaving-home step; see [`weather-forecast.md`](references/weather-forecast.md) and [`references/scene-workflow/recommend.md`](references/scene-workflow/recommend.md), not other business. Full list: [`SKILL.md`](SKILL.md) -> **Out of Scope**.
