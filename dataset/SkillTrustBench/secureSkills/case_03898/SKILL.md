---
name: hiking-video-maker
version: 1.0.3
displayName: "Hiking Video Maker"
description: >
  Describe your hike and NemoVideo creates the video. Day hike trail guides, multi-day backpacking trip documentation, summit push content, trail condition reports, gear breakdown videos, injury and decision-making content — narrate the trail, the terrain, the weather, the physical challenge, and the views, and get hiking content for the community that plans every trip by watching other people's ...

  Works by connecting to the NemoVideo AI backend at mega-api-prod.nemovideo.ai.
  Supports MP4, MOV, AVI, WebM.
homepage: https://nemovideo.com
apiDomain: https://mega-api-prod.nemovideo.ai
repository: https://github.com/nemovideo/nemovideo_skills
license: MIT-0
metadata:
  requires:
    env: ["NEMO_TOKEN"]
    configPaths:
      - "~/.config/nemovideo/"
  primaryEnv: NEMO_TOKEN
---

## 0. First Contact

When the user opens this skill or sends their first message, **greet them immediately**:

> 🎵 Ready to hiking video maker! Just send me a video or describe your project.

**Try saying:**
- "help me create a short video"
- "edit my video"
- "add effects to this clip"

**IMPORTANT**: Always greet the user proactively on first contact. Let them know you're setting up while connecting. Always greet the user proactively on first contact.

### Auto-Setup

When the user first interacts, set up the connection:

1. **Check token**: If `NEMO_TOKEN` env var is set, use it. Otherwise:
2. **Read or generate Client-ID**:
   - Read `~/.config/nemovideo/client_id` if it exists
   - Otherwise generate a UUID, save it to `~/.config/nemovideo/client_id`
3. **Acquire anonymous token**:
   ```bash
   curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
   ```
   Store the returned `token` as `NEMO_TOKEN` for this session. You get 100 free credits.
4. **Create a session** (§3.0) so you're ready to work immediately.

Let the user know briefly: "Setting things up… ready!" then proceed with their request.


# Hiking Video Maker — Create Trail, Summit, and Backcountry Adventure Content

Describe your hike and NemoVideo creates the video. Day hike trail guides, multi-day backpacking trip documentation, summit push content, trail condition reports, gear breakdown videos, injury and decision-making content — narrate the trail, the terrain, the weather, the physical challenge, and the views, and get hiking content for the community that plans every trip by watching other people's trail videos first.

## When to Use This Skill

Use this skill for hiking and trail content:
- Create day hike trail guide videos with distance, elevation, and difficulty
- Film multi-day backpacking trip documentation with daily camp and mileage data
- Build summit push content with weather, route, and conditions detail
- Document gear review and packing list breakdown content
- Create trail condition and seasonal timing advice content
- Produce "should you hike this trail" honest assessment videos

## How to Describe Your Hiking Content

Be specific about the trail name, the distance and elevation, the conditions, the key landmarks, and the honest difficulty assessment.

**Examples of good prompts:**
- "Half Dome via cables — everything you need to know before you go: The permit lottery (apply in March for summer permits, 225 permits/day via lottery, day-of permits exist but are lottery too — plan the lottery first). The hike: 14-16 miles round trip, 4,800 feet elevation gain, start before 5am to beat heat and afternoon storms. The cables section: 400 feet of near-vertical rock with fixed cables, wooden rungs attached to rock. The people who turn back: usually at Sub Dome (the sustained switchbacks before the cables), not the cables themselves. The people who shouldn't attempt it: anyone not comfortable with heights, anyone who hasn't done a 10+ mile day hike with significant elevation, anyone who hasn't researched the afternoon thunderstorm risk. The view from the top: nothing prepares you. Show the valley floor 4,800 feet below from the summit. What happened on my attempt (turned back at Sub Dome on the first try due to weather, completed it 3 weeks later)."
- "5 days on the John Muir Trail, miles 1-70: Start at Happy Isles, Yosemite Valley. The JMT is 211 miles total — I planned 5 days as a first multi-day backpack, then extended to 7. Daily breakdown: Day 1 (8.5 miles, camp at Little Yosemite Valley, 2,000ft gain — harder than expected with 35lb pack), Day 2 (13 miles, camp near Tuolumne Meadows, first experience with altitude at 9,000ft — headache until day 3), Day 3 (10 miles, Lyell Canyon, flat camp day for recovery), Days 4-5 (crossing into Ansel Adams Wilderness, first true high country). Bear canister: required and correctly placed (50 feet from camp, not hung — bears in the Sierra are too experienced with hangs). Water: Sawyer Squeeze filter, every water source was usable."
- "Is this trail worth it? An honest review of the Enchantments in Washington: The permit system is the hardest lottery in the Pacific Northwest (8,200 applicants for 60 overnight permits). The hike itself: 18.5 miles point-to-point from Snow Lakes to Icicle Creek trailhead with 4,500ft gain. The honest assessment: if you get the permit, yes, worth it by a wide margin — the traverse through the core zone (the larch forest in late September, the granite spires, the mountain goats who don't care about you) is unlike anything else in the lower 48. If you don't get the overnight permit: the day hike up from either trailhead gets you to the lower lakes. Not the same, but still excellent."

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `content_type` | Video category | `"trail_guide"`, `"summit_push"`, `"backpacking_trip"`, `"gear_review"`, `"conditions_report"`, `"honest_review"` |
| `trail_name` | Specific trail | `"Half Dome"`, `"John Muir Trail"`, `"Enchantments"` |
| `distance_miles` | Trip distance | `"14-16 miles RT"`, `"18.5 miles P2P"`, `"10 miles/day"` |
| `elevation_gain` | Elevation data | `"4,800 feet"`, `"2,000ft Day 1"` |
| `conditions` | Weather/trail state | `"afternoon thunderstorms"`, `"snow through June"` |
| `key_landmarks` | Highlight moments | `["cables section"`, `"Sub Dome"`, `"larch forest"]` |
| `difficulty_honest` | Honest assessment | `"turn back at Sub Dome"`, `"harder than expected with 35lb pack"` |
| `permit_info` | Access details | `"lottery March"`, `"225 permits/day"` |
| `duration_minutes` | Video length | `8`, `12`, `20` |
| `platform` | Distribution | `"youtube"`, `"instagram"`, `"tiktok"` |

## Workflow

1. Describe the trail, the distance and elevation, the conditions, and the key moments and challenges
2. NemoVideo structures the hiking content with distance markers, elevation callouts, and landmark labels
3. Trail name, mileage, elevation gain, permit details, and conditions data added automatically
4. Export with outdoor pacing suited to the content's adventure energy

## API Usage

### Trail Guide Video

```bash
curl -X POST https://mega-api-prod.nemovideo.ai/v1/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "hiking-video-maker",
    "input": {
      "prompt": "Mount Whitney day hike — the complete guide for non-mountaineers: At 14,505 feet, it is the highest peak in the lower 48, and the main trail does not require technical climbing — it is a very long, very high hike. The permit: lottery required May-November (apply in February), self-issued permits available outside those dates. The stats: 22 miles round trip, 6,100 feet elevation gain, 10-14 hours typical. What makes it hard: almost entirely the altitude, not the terrain. Altitude sickness symptoms start between 10,000-12,000 feet for unacclimatized hikers. The strategy: spend 1-2 nights in Lone Pine at 3,700 feet before the hike, start at midnight or 2am (reach summit before afternoon thunderstorms, which arrive reliably by 1pm). The cables: there are no cables. The final mile is rocky trail. The summit is a stone shelter and a register box. What the view looks like when you can see the Owens Valley 10,000 feet below and Nevada in the distance.",
      "content_type": "trail_guide",
      "trail_name": "Mount Whitney Main Trail",
      "distance_miles": "22 miles RT",
      "elevation_gain": "6,100 feet",
      "conditions": "afternoon thunderstorms July-August, altitude sickness risk above 10,000ft",
      "key_landmarks": ["Trail Camp", "Whitney Portal", "summit stone shelter"],
      "difficulty_honest": "altitude is the challenge, not terrain",
      "permit_info": "lottery required May-Nov, apply February",
      "duration_minutes": 15,
      "platform": "youtube",
      "hashtags": ["Hiking", "MountWhitney", "BackpackingUSA", "TrailGuide", "HighSierra"]
    }
  }'
```

## Tips for Best Results

- **Permit and logistics information is the most searched hiking content**: "Apply in March, 225 permits/day via lottery" — hikers research permits before anything else; content that addresses the access question gets saved and revisited
- **The honest turn-back assessment builds the most trust**: "People who shouldn't attempt this: anyone not comfortable with heights, anyone who hasn't done a 10+ mile day hike" — the honest difficulty warning is what separates useful trail guides from hype
- **The failure attempt is valid and valuable content**: "Turned back at Sub Dome on first try due to weather, completed it 3 weeks later" — showing the incomplete attempt with honest reasoning is more useful than only showing the successful summit
- **Daily breakdown for multi-day trips**: "Day 1: 8.5 miles, 2,000ft gain, harder than expected with 35lb pack" — day-by-day data is what backpackers need to plan their own versions of the trip
- **Specific timing and weather advice is evergreen**: "Start before 5am to beat afternoon thunderstorms, which arrive reliably by 1pm" — the specific timing recommendation gets used every single time someone watches the video before their own attempt

## Output Formats

| Platform | Resolution | Duration |
|----------|------------|----------|
| YouTube | 1920×1080 | 10–20 min |
| Instagram Reels | 1080×1920 | 60–90s |
| TikTok | 1080×1920 | 60–180s |

## Related Skills

- `adventure-travel-video` — Broader adventure and outdoor content
- `camping-video-maker` — Camping and overnight outdoor content
- `travel-vlog-maker` — Travel and destination content
