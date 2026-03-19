import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

# This code transform a feed.atom exported from blogspot, and convert it
# to a sequence of htmls, one per post.
# It also produces a index.html with a table containing all post links

INPUT_XML = "feed.atom"
OUTPUT_DIR = "sagme"
posts_index = []

ns = {
    "atom": "http://www.w3.org/2005/Atom",
    "blogger": "http://schemas.google.com/blogger/2018"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or "post"

def is_post(entry):
    t = entry.find("blogger:type", ns)
    return t is not None and t.text == "POST"

def is_published(entry):
    status = entry.find("blogger:status", ns)
    if status is None:
        return True
    return status.text == "LIVE"   # skip SCHEDULED, DRAFT

def get_labels(entry):
    labels = []
    for cat in entry.findall("atom:category", ns):
        term = cat.attrib.get("term", "")
        scheme = cat.attrib.get("scheme", "")
        # Keep only user labels (your case uses blogger scheme)
        if scheme.startswith("tag:blogger.com"):
            labels.append(term)
    return labels

def get_date(entry):
    pub = entry.find("atom:published", ns)
    created = entry.find("blogger:created", ns)

    date_source = pub if pub is not None else created
    if date_source is None:
        return ""

    try:
        dt = datetime.fromisoformat(date_source.text.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_source.text

#####################################################################
## this code uses images at Sagme's GitHub, but not all images following the same
## name format, so I'll keep pointing, for now, to the original google images

# BASE = "https://raw.githubusercontent.com/jpneto/Images/refs/heads/main/sagme/"

# def rewrite_image_urls(html):
#     def replace(match):
#         full_url = match.group(1)
#         if "googleusercontent.com" not in full_url:
#             return match.group(0)
#         filename = full_url.split("/")[-1].split("?")[0]
#         return f'src="{BASE}{filename}"'
#     return re.sub(r'src="([^"]+)"', replace, html)

# def rewrite_image_hrefs(html):
#     def replace(match):
#         full_url = match.group(1)
#         if "googleusercontent.com" not in full_url:
#             return match.group(0)
#         filename = full_url.split("/")[-1].split("?")[0]
#         return f'href="{BASE}{filename}"'
#     return re.sub(r'href="([^"]+)"', replace, html)
#####################################################################

tree = ET.parse(INPUT_XML)
root = tree.getroot()

for entry in root.findall("atom:entry", ns):

    if not is_post(entry):
        continue

    # if not is_published(entry):
    #     continue  # skip scheduled/drafts

    title_el = entry.find("atom:title", ns)
    content_el = entry.find("atom:content", ns)

    if title_el is None or content_el is None:
        continue

    title = title_el.text or "Untitled"
    content = content_el.text or ""
    
    ## read above
    # content = rewrite_image_urls(content)  
    # content = rewrite_image_hrefs(content)

    date_str = get_date(entry)
    labels = get_labels(entry)

    tags_html = ""
    if labels:
        tags_html = "<b>Tags:</b> " + ", ".join(labels)

    filename = slugify(title) + ".html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    html = f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta name="author" content="João Pedro Neto">
  <title>{title}</title>
</head>

<body background="../back-wood3.jpg">

  <h2>{title}</h2>
  <b>Date:</b> {date_str} | {tags_html}
  <hr>

{content}

</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
        posts_index.append({
            "title": title,
            "filename": filename,
            "date": date_str,
            "tags": labels
        })

print("Done! Files generated in:", OUTPUT_DIR)

#####################################################################
### Make index.html ###

# Sort posts by date (newest first)
posts_index.sort(key=lambda x: x["date"], reverse=True)

index_rows = []

for post in posts_index:
    tags = ", ".join(post["tags"]) if post["tags"] else ""
    row = f"""
  <tr>
    <td>{post['date']}</td>
    <td>{tags}</td>
    <td><a href="{OUTPUT_DIR}/{post['filename']}">{post['title']}</a></td>
  </tr>
"""
    index_rows.append(row)

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="author" content="João Pedro Neto">
  <title>Blog Index</title>
</head>

<body background="back-wood3.jpg">
<h2>Posts</h2>

<table border="1" cellspacing="0" cellpadding="5">
  <tr>
    <th>Date</th>
    <th>Tags</th>
    <th>Post</th>
  </tr>
  {''.join(index_rows)}
</table>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

#####################################################################

### Make a Javascript list to use with WAG's dynamic table ###

index_rows = []

for post in posts_index:
    tags = ", ".join(post["tags"]) if post["tags"] else ""
    row = f"""      {{
        date: "{post['date']}",
        tags: "{tags}",
        url: "{post['filename']}",
        linkName: "{post['title']}"
      }},
"""
    index_rows.append(row)

index_js = f"""
        {''.join(index_rows)} 
"""

with open(os.path.join(OUTPUT_DIR, "..\\table.js"), "w", encoding="utf-8") as f:
    f.write(index_js)