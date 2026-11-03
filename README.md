# Instagram Public Profile & Post Scraper (Max 250 Posts/Profile)

This Apify Actor extracts comprehensive public post data from Instagram profiles using `apify/instagram-scraper`, enforcing a **strict cap of the last 250 posts per account**.

## Default Target Accounts

By default, the Actor is pre-configured to scrape the last **250 posts** from each of the following 5 Paraguayan RE/MAX Instagram profiles:

1. `https://www.instagram.com/remaxconexionpy_/`
2. `https://www.instagram.com/rblack.py/`
3. `https://www.instagram.com/remaxelitepy/`
4. `https://www.instagram.com/remaxrealtypy/`
5. `https://www.instagram.com/remaxselection/`

## Extracted Data Fields (Per Post)

Every post pushed to the default Dataset is validated and normalized into the following structure:

| Category | Fields Extracted |
| :--- | :--- |
| **Identifiers & Links** | `id`, `shortCode`, `url`, `inputUrl`, `timestamp` (UTC ISO-8601) |
| **Content & Media Formats** | `type` (`Image`, `Video`, `Sidecar`), `productType` (`clips`, `feed`, etc.), `caption`, `alt`, `displayUrl`, `videoUrl`, `videoDuration`, `images`, `childPosts` (nested carousel slides) |
| **Public Engagement Metrics** | `likesCount`, `commentsCount`, `videoViewCount`, `videoPlayCount` |
| **Authorship & Collaborators** | `ownerUsername`, `ownerFullName`, `ownerId`, `coauthorProducers`, `taggedUsers` |
| **Taxonomy & Geolocation** | `hashtags` (`#`), `mentions` (`@`), `locationName`, `locationId` |
| **Music & Audio** | `musicInfo` (track name, artist, audio ID, original audio flag) |
| **Comments & Status** | `firstComment`, `latestComments` (comment text, author, timestamp, likes), `isPinned`, `isSponsored` |

> **Note on Private Metrics**: Private Instagram Insights (Unique Reach, Total Impressions, Saves, Shares, Reel Retention curves, and Profile Clicks) are only accessible to account owners via the official Meta Graph API and are not exposed publicly.

## Input Configuration (`.actor/input_schema.json`)

- **`profile_urls`** (`array` of `string`, required): Public Instagram profile URLs to scrape.
- **`results_limit`** (`integer`, default `250`, min `1`, max `250`): Maximum number of recent posts to scrape per profile. Any value above `250` is automatically clamped to `250`.
- **`actor_id`** (`string`, default `"apify/instagram-scraper"`): Upstream Apify Store Actor ID used to perform the extraction.
- **`add_parent_data`** (`boolean`, default `true`): Whether to include parent profile metadata on each post record.

## Output & Storage

- **Default Dataset (`.actor/dataset_schema.json`)**: Contains all normalized post items with a structured table view (`Instagram Posts Overview`).
- **Default Key-Value Store (`.actor/key_value_store_schema.json`)**: Saves a `SUMMARY` JSON record containing `status`, `maxPostsPerProfileCap` (`250`), `totalPostsExtracted`, and the `postsPerAccount` tally.

## Project Structure

```text
.actor/
├── actor.json                  # Actor configuration & schema links
├── dataset_schema.json         # Dataset schema covering all 30 extracted post fields
├── input_schema.json           # Input form & validation (5 accounts, 250 post cap)
├── key_value_store_schema.json # Key-value store schema for the SUMMARY record
└── output_schema.json          # Output links for Dataset items and SUMMARY
my_actor/
├── __main__.py                 # Module execution entry point
├── main.py                     # Actor orchestration, abort handling & 250-post cap enforcement
└── routes.py                   # Data normalization & type-checking for Instagram post fields
Dockerfile                      # Container image definition
requirements.txt                # Python dependencies
```

## Running Locally or on Apify

1. Ensure your `APIFY_TOKEN` is configured (or run `apify login`).
2. Run locally with:
   ```bash
   apify run
   ```
3. Or deploy to Apify Console:
   ```bash
   apify push
   ```
