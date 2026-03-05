# Portrait Verification & Reference Image Strategies — Zero Tolerance Policy

## Problem Statement

AI-generated oil painting portraits can show the wrong person due to:
1. **Caching bugs** — same image copied to multiple filenames (Tor Bergeron bug — 19 portraits affected)
2. **Hallucinated research data** — AI confuses subject with another person of same name (Mark Fisher → wrong "Mark Fisher")
3. **Gender errors** — without reference photo, AI defaults to era-typical stereotypes (Eugenia Kalnay shown as man)
4. **Wrong dates** — AI hallucinates birth/death years (Lance Wallace shown as "1975-Present" instead of "1940-2022")
5. **Wrong era styling** — clothing/hair not matching historical period (Richard Carrington in modern style)
6. **Name confusion** — wrong first name (Mark vs. Mike Fisher)
7. **Too generic** — portrait doesn't resemble the actual person (David Lary, John Pyle)

---

## Part 1: Reference Image Sources (Comprehensive)

### Tier 1: Direct Institutional Sources (Highest Authenticity)

#### 1.1 University Faculty Pages
Every living academic has a department faculty page with photo:
```
URL patterns to try:
- https://www.{dept}.cam.ac.uk/people/{firstname}-{lastname}
- https://www.{dept}.ox.ac.uk/people/{lastname}
- https://www.atmos.umd.edu/people/{last}
- https://profiles.utdallas.edu/{Name}
- https://profiles.stanford.edu/{Name}
- https://eecs.berkeley.edu/research/faculty/{Name}
- https://www.imperial.ac.uk/people/{Name}
- https://www.reading.ac.uk/met/staff/{Name}

Web search: site:{university_domain} "{first_name} {last_name}" portrait photo
```

**Confirmed successful URLs:**
| Person | Institution | URL |
|--------|------------|-----|
| John Pyle | Cambridge Chem | `https://www.ch.cam.ac.uk/files/styles/staff_portrait/public/portraits/jap12.jpg` |
| John Pyle | Cambridge CCS | `https://www.climatescience.cam.ac.uk/sites/.../john.pyle.jpg` |
| John Pyle | St Catharine's | `https://www.caths.cam.ac.uk/sites/.../John%20Pyle%20new%20portraits...jpg` |
| David Lary | UT Dallas | `https://profiles.utdallas.edu/storage/media/3494/conversions/DavidLary-medium.jpg` |
| Eugenia Kalnay | NASA GSFC | `https://earth.gsfc.nasa.gov/sites/.../eugeniaKalnay.png` |
| Ulrich Platt | Heidelberg | `https://www.uni-heidelberg.de/md/einrichtungen/mk/fellows/portrait_platt_04.jpg` |
| Andrew Lorenc | Surrey/RMS | `https://blogs.surrey.ac.uk/mathsresearch/wp-content/.../Lorenc.jpg` |
| Clive Rodgers | Oxford Jesus | `https://www.jesus.ox.ac.uk/wp-content/.../Rodgers-Clive-crop-540x400.jpg` |

#### 1.2 Research Institute Staff Directories
```
- ECMWF: https://www.ecmwf.int/en/research/staff/{name}
- NCAR/UCAR: https://staff.ucar.edu/browse/people/
- Max Planck Institute: https://www.mpic.de/
- DTU Space: https://orbit.dtu.dk/en/persons/
- NASA JPL: https://www.jpl.nasa.gov/people/
- NOAA GML: https://gml.noaa.gov/
- UK Met Office: https://www.metoffice.gov.uk/research/people/
- ECMWF: https://www.ecmwf.int/en/search/{name}
```

**Confirmed DTU:** Henrik Svensmark: `https://orbit.dtu.dk/files-asset/399006805/38287_bccf27f8.jpg`

#### 1.3 Award and Prize Pages (Often Has Professional Photos)
```
- Nobel Prize: https://www.nobelprize.org/prizes/chemistry/{year}/laureates/
- Royal Meteorological Society awards
- AMS awards: https://www.ametsoc.org/index.cfm/ams/about-ams/ams-awards-fellowships/
- AGU awards: https://www.agu.org/honors/
- Kyoto Prize: https://www.inamori-f.or.jp/en/laureates/
- IEEE Awards: https://www.ieee.org/content/dam/ieee-org/ieee/web/org/about/awards/
```

### Tier 2: Online Academic Profiles

#### 2.1 Wikipedia (Photo in Summary API)
```python
# API returns thumbnail URL
url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ','_')}"
# Returns: {"thumbnail": {"source": "https://upload.wikimedia.org/.../...jpg"}}
```
**Coverage:** ~70% of historical scientists, ~40% of living scientists

#### 2.2 ResearchGate Profile Photos
```
URL: https://www.researchgate.net/profile/{FirstName-LastName}
# Or search: site:researchgate.net "{first_name} {last_name}"
```
**Coverage:** ~75% of active researchers (post-1970)

#### 2.3 Google Scholar Profiles
```
URL: https://scholar.google.com/citations?user={ID}
# ID from web search: site:scholar.google.com "{name}"
```
**Coverage:** ~60% of academics

#### 2.4 ORCID Profiles
```
URL: https://orcid.org/{ORCID-ID}
# Search: https://pub.orcid.org/v3.0/search/?q=family-name:{lastname}+given-names:{firstname}
```

#### 2.5 LinkedIn (For Living Scientists)
```
URL: https://www.linkedin.com/in/{name-variant}
# Many scientists have LinkedIn with professional headshots
```

### Tier 3: Academic Database Photos

#### 3.1 Journal Author Photos in Papers (Post-1990)
Many journals include author headshots:
- **Quarterly Journal of the Royal Meteorological Society (QJRMS)**
- **Atmospheric Chemistry and Physics (ACP)**
- **Nature** and **Science** (biographical notes)
- **Geophysical Research Letters**
- **Journal of Geophysical Research**
- **Bulletin of the AMS**

```python
# Approach:
# 1. Get DOI from bibliography
# 2. Use Unpaywall API to get PDF URL
# 3. Use pdfimages to extract images from PDF
# 4. Use Gemini Vision to identify which image is the author photo
import subprocess
pdf_images_cmd = f"pdfimages -j {pdf_file} {output_prefix}"
```

**Fisher & Lary 1995 QJRMS paper** may contain author photos of both Mike Fisher and David Lary.

#### 3.2 AIP (American Institute of Physics) Oral History Archives
Excellent source for 20th century physicists and atmospheric scientists:
```
URL: https://www.aip.org/history-programs/niels-bohr-library/oral-histories/
Search: https://www.aip.org/history/catalog/search?q={name}
```
**Coverage:** Many atmospheric scientists, cosmic ray researchers

#### 3.3 AMS (American Meteorological Society) Hall of Fame
```
URL: https://www.ametsoc.org/index.cfm/ams/about-ams/ams-awards-fellowships/ams-fellows/
```

#### 3.4 National Academy of Sciences Member Profiles
```
URL: https://www.nasonline.org/member-directory/members/{name}.html
```

### Tier 4: Historical Archives

#### 4.1 University Archives and Library Digital Collections
- MIT Archives (Norbert Wiener)
- ETH Zurich Archives (Kalman, Einstein)
- Imperial College London Archives
- Cambridge Digital Library
- Oxford Digital Collections
- Uppsala University (Tor Bergeron)

```
URL pattern: https://archives.{university}.edu/search?q={name}
```

#### 4.2 National Portrait Galleries
```
- National Portrait Gallery UK: https://www.npg.org.uk/collections/search/portrait/
- Smithsonian National Portrait Gallery: https://npg.si.edu/search/artworks
- National Portrait Gallery Australia
```

#### 4.3 Wikimedia Commons (High Resolution Historical Photos)
```
URL: https://commons.wikimedia.org/wiki/Category:{Name}
Search API: https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={name}
```

#### 4.4 Europeana (European Cultural Heritage)
```
URL: https://www.europeana.eu/en/search?query={name}
```

#### 4.5 Library of Congress Digital Collections
```
URL: https://www.loc.gov/pictures/search/?q={name}
```

### Tier 5: Scientific Society Photos

#### 5.1 Royal Meteorological Society (RMetS)
```
URL: https://www.rmets.org/
Award pages often include recipient photos
```

#### 5.2 American Meteorological Society (AMS)
```
URL: https://www.ametsoc.org/
```

#### 5.3 European Geosciences Union (EGU)
```
URL: https://www.egu.eu/awards-medals/
```

#### 5.4 International Union of Geodesy and Geophysics (IUGG)

#### 5.5 IEEE (for Kalman and signal processing pioneers)
```
URL: https://ieeexplore.ieee.org/author/{name}
```

---

## Part 2: Verification Strategies

### Strategy 1: MD5 Hash Duplicate Detection (AUTOMATED, INSTANT)
```bash
md5 Figures/Portraits/*_Painting.png | sort | awk '{print $1}' | sort | uniq -d
```
**Detects:** Identical portrait files (caching bugs). **Certainty: 100%.**

### Strategy 2: File Size Anomaly Detection (AUTOMATED, INSTANT)
```bash
ls -la Figures/Portraits/*_Painting.png | awk '{print $5, $NF}' | sort -n
```
**Detects:** Placeholder images (<100 KB) or suspicious uniformity (all exactly same size).

### Strategy 3: Portrait Overlay Text OCR (AUTOMATED)
Extract and verify the name/dates shown in the portrait overlay:
```python
import google.generativeai as genai
model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content([
    'Read the text overlay at the bottom of this portrait. Return JSON: {"name": str, "years": str}',
    {"mime_type": "image/png", "data": portrait_bytes}
])
# Verify extracted dates match expected birth/death years
```
**Detects:** Hallucinated dates (Lance Wallace "1975-Present" should be "1940-2022").

### Strategy 4: Wikipedia Reference Photo Comparison (AUTOMATED + AI VISION)
For each portrait, download Wikipedia thumbnail and compare with Gemini Vision.
**Detects:** Wrong gender, wrong ethnicity, wrong era. **Coverage: ~70%.**

### Strategy 5: Institutional Photo Comparison (SEMI-AUTOMATED)
For living scientists, download their institutional photo and compare with generated portrait.
**Detects:** Wrong likeness, wrong gender. **Coverage: ~90% of modern scientists.**

### Strategy 6: Multi-Source Reference Aggregation (COMPREHENSIVE)
For each person, search ALL applicable sources from Part 1 and collect the best 2-3 photos.
Use ALL collected photos simultaneously as references when generating the portrait.

### Strategy 7: Ground Truth Biographical Cross-Check (AI REASONING)
Ask Gemini to verify gender, era, nationality, and appearance consistency.

### Strategy 8: Journal Paper Author Photo Extraction (TARGETED)
For scientists where institutional photos fail, extract author headshots from their papers.

### Strategy 9: Name Disambiguation Verification (CRITICAL)
Before generating any portrait:
1. Cross-check the exact first name against the citation (e.g., "Fisher, M" → search for full name)
2. Search for "Mike Fisher ECMWF meteorologist" vs generic "Mark Fisher"
3. Verify there's only one famous scientist with that name, or be explicit about which one

### Strategy 10: Human Visual Spot-Check (MANDATORY FINAL GATE)
The author personally reviews each portrait for people they know:
- David Lary (himself)
- Mike Fisher (ECMWF colleague)
- John Pyle (known colleague from atmospheric chemistry community)

---

## Part 3: Portrait Generation Pipeline (Zero-Tolerance)

```
Step 1: NAME CHECK
  - Verify exact full first+last name from citation/text
  - Search for disambiguation (multiple famous people with same name?)
  - Confirm institution and field match expected person

Step 2: MULTI-SOURCE PHOTO COLLECTION
  - Wikipedia API → thumbnail photo
  - Institutional faculty page → professional headshot
  - ResearchGate / Google Scholar → profile photo
  - Award pages → official portrait
  - Journal papers → author headshot
  - AIP/Archives → historical photo (for historical figures)

Step 3: PORTRAIT GENERATION (with reference photos)
  - Use SubjectData with EXPLICIT gender in era description
  - Inject ALL found reference photos into PortraitClient
  - Override find_reference_images AND download_and_prepare_references
  - Use fresh PortraitClient per person with unique temp directory

Step 4: AUTOMATED VERIFICATION
  - MD5 hash check (no duplicates)
  - File size check (>500 KB)
  - OCR: dates in overlay match expected birth/death years
  - Gemini Vision comparison against reference photo(s)
  - Gender check
  - Era appropriateness check

Step 5: HUMAN REVIEW
  - Author reviews all portraits of people they personally know
  - Compare generated portrait against reference photo for all others
  - Flag any that look wrong for regeneration

Step 6: RE-GENERATION LOOP
  - Any failed portrait → delete → return to Step 2
  - Try additional reference sources if first attempt failed
  - Maximum 3 attempts before flagging for manual intervention
```

---

## Part 4: Confirmed Photo URLs (Verified HTTP 200)

| Person | Source | URL |
|--------|--------|-----|
| John Pyle | Cambridge Chem Dept | `https://www.ch.cam.ac.uk/files/styles/staff_portrait/public/portraits/jap12.jpg` |
| John Pyle | Cambridge CCS | `https://www.climatescience.cam.ac.uk/sites/default/files/styles/inline/public/media/profile/john.pyle.jpg` |
| John Pyle | St Catharine's | `https://www.caths.cam.ac.uk/sites/default/files/styles/profile_image/public/John%20Pyle%20new%20portraits-5331%20-%20Copy_0.jpg` |
| David Lary | UT Dallas Profile | `https://profiles.utdallas.edu/storage/media/3494/conversions/DavidLary-medium.jpg` |
| Eugenia Kalnay | NASA GSFC | `https://earth.gsfc.nasa.gov/sites/default/files/styles/max_325x325/public/maniacs/pics/eugeniaKalnay.png` |
| Ulrich Platt | Heidelberg Marsilius | `https://www.uni-heidelberg.de/md/einrichtungen/mk/fellows/portrait_platt_04.jpg` |
| Henrik Svensmark | DTU Orbit | `https://orbit.dtu.dk/files-asset/399006805/38287_bccf27f8.jpg` |
| Andrew Lorenc | Surrey/RMS blog | `https://blogs.surrey.ac.uk/mathsresearch/wp-content/uploads/sites/11/2022/06/Lorenc.jpg` |
| Clive Rodgers | Jesus College Oxford | `https://www.jesus.ox.ac.uk/wp-content/uploads/2021/04/Rodgers-Clive-crop-540x400.jpg` |
| Mike Fisher | **NOT FOUND** | — (ECMWF does not publish staff photos publicly) |

---

## Part 5: Lessons Learned (DO NOT REPEAT)

1. **Never share PortraitClient instances between people** — caching bug copies portrait 1 to all others
2. **Gender must be EXPLICIT in era description** — AI defaults to era-stereotyped gender
3. **Wikipedia verification can match the WRONG person** — "Mark Fisher" matched a celebrity, not the ECMWF meteorologist
4. **"M. Fisher" ≠ "Mark Fisher"** — always find the full first name from the actual citation
5. **4 KB images are rejected** — minimum image size is 256×256 px (~10+ KB for JPEG)
6. **Always override BOTH** `find_reference_images` AND `download_and_prepare_references` for proper injection
7. **Verify names in both the portrait text overlay AND the LaTeX source** — both must be correct
8. **The PortraitClient evaluator scoring is unreliable** — "FAILED (score: 0.85)" doesn't mean the portrait is bad; it means it's below the 0.90 internal threshold but the portrait is still acceptable

---

## Part 6: Scripts Reference

| Script | Purpose | Location |
|--------|---------|---------|
| `verify_all_portraits.py` | Gemini Vision verification with Wikipedia photos | `/tmp/verify_all_portraits.py` |
| `regenerate_correct_portraits.py` | Fix 19 Tor-Bergeron-duplicate portraits | `/tmp/regenerate_correct_portraits.py` |
| `fix_failed_portraits.py` | Fix 4 portraits that failed verification | `/tmp/fix_failed_portraits.py` |
| `regenerate_with_real_photos.py` | Regenerate 7 portraits with institutional photos | `/tmp/regenerate_with_real_photos.py` |
| `generate_mike_fisher.py` | Generate Mike Fisher (no public photo available) | `/tmp/generate_mike_fisher.py` |
| `fix_john_pyle.py` | Regenerate John Pyle with better Cambridge URL | `/tmp/fix_john_pyle.py` |
