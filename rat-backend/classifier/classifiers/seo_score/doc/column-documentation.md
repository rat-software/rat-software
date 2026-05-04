# CSV Column Documentation

## Base Data Columns (results.csv)

These columns are from the original results CSV file:

1. `id`
   - Description: Unique identifier for each entry
   - Type: Integer
   - Example: 81

2. `created_at`
   - Description: Timestamp of when the entry was created
   - Type: Datetime string
   - Example: "2024-12-12 13:27:57.552239"

3. `url`
   - Description: Full URL of the analyzed webpage
   - Type: String
   - Example: "https://www.example.com/page"

4. `main`
   - Description: Main domain URL of the website
   - Type: String
   - Example: "https://www.example.com/"

5. `name`
   - Description: Source identifier
   - Type: String
   - Example: "bing_de.py"

6. `ip`
   - Description: IP address of the server
   - Type: String
   - Example: "92.205.212.128"

7. `position`
   - Description: Ranking position of the result
   - Type: Integer
   - Example: 1

8. `title`
   - Description: Page title
   - Type: String
   - Example: "Page Title - Website Name"

9. `description`
   - Description: Meta description or snippet of the page
   - Type: String
   - Example: "Page description text..."

10. `query`
    - Description: Search query used to find the page
    - Type: String
    - Example: "search term"

## SEO Analysis Columns (classifier_results.csv)

These columns contain detailed SEO analysis metrics:

1. `class_res`
   - Description: Overall SEO score
   - Type: Float
   - Range: 0-100
   - Example: 92.28

2. `analysis_explanation`
   - Description: Detailed explanation of the SEO score calculation
   - Type: String
   - Example: "Analytics tools detected (+5 points). Page loading time: 1.1s..."

3. `canonical`
   - Description: Presence of canonical tag
   - Type: Binary (0/1)
   - Example: 1

4. `category_content_quality`
   - Description: Content quality score
   - Type: Float
   - Range: 0-100
   - Example: 70.6

5. `category_meta_elements`
   - Description: Meta elements score
   - Type: Float
   - Range: 0-100
   - Example: 82.0

6. `category_technical_seo`
   - Description: Technical SEO score
   - Type: Float
   - Range: 0-100
   - Example: 100

7. `category_user_experience`
   - Description: User experience score
   - Type: Float
   - Range: 0-100
   - Example: 94.0

8. `content_length_score`
   - Description: Score based on content length
   - Type: Integer
   - Range: 0-100
   - Example: 60

9. `description_score`
   - Description: Quality score of the meta description
   - Type: Integer
   - Range: 0-100
   - Example: 80

10. `description_text`
    - Description: Actual meta description text
    - Type: String
    - Example: "Page description..."

11. `external_link_count`
    - Description: Number of outbound links
    - Type: Integer
    - Example: 44

12. `external_links`
    - Description: Quality score of external links
    - Type: Integer
    - Example: 25

13. `h1`
    - Description: Presence of H1 tag
    - Type: Binary (0/1)
    - Example: 1

14. `heading_structure_score`
    - Description: Score for heading hierarchy
    - Type: Integer
    - Range: 0-100
    - Example: 100

15. `https`
    - Description: Whether the site uses HTTPS
    - Type: Boolean
    - Example: True

16. `image_optimization_score`
    - Description: Score for image optimization
    - Type: Integer
    - Range: 0-100
    - Example: 63

17. `internal_link_count`
    - Description: Number of internal links
    - Type: Integer
    - Example: 94

18. `internal_links`
    - Description: Quality score of internal links
    - Type: Integer
    - Example: 113

19. `keyword_optimization_reasons`
    - Description: List of keyword optimization findings
    - Type: JSON array
    - Example: []

20. `keyword_optimization_score`
    - Description: Score for keyword usage
    - Type: Integer
    - Range: 0-100
    - Example: 0

21. `link_quality_score`
    - Description: Overall link quality score
    - Type: Integer
    - Range: 0-100
    - Example: 100

22. `loading_time`
    - Description: Page load time in seconds
    - Type: Float
    - Example: 1.123

23. `micros`
    - Description: List of microdata formats detected
    - Type: JSON array
    - Example: ["schema.org", "rel-tag"]

24. `navigation_score`
    - Description: Score for navigation structure
    - Type: Integer
    - Range: 0-100
    - Example: 70

25. `nofollow`
    - Description: Count of nofollow links
    - Type: Integer
    - Example: 0

26. `og`
    - Description: Presence of OpenGraph tags
    - Type: Binary (0/1)
    - Example: 0

27. `robots_txt`
    - Description: Presence of robots.txt file
    - Type: Binary (0/1)
    - Example: 1

28. `seo_classification`
    - Description: Overall SEO classification
    - Type: String
    - Example: "most_probably_optimized"

29. `sitemap`
    - Description: Presence of sitemap
    - Type: Binary (0/1)
    - Example: 1

30. `social_tags`
    - Description: JSON object containing social media meta tags
    - Type: JSON object
    - Example: {"og_tags": [], "twitter_tags": ["twitter:card"]}

31. `social_tags_score`
    - Description: Score for social media optimization
    - Type: Integer
    - Range: 0-100
    - Example: 50

32. `title_score`
    - Description: Quality score of the page title
    - Type: Integer
    - Range: 0-100
    - Example: 60

33. `title_text`
    - Description: Actual page title text
    - Type: String
    - Example: "Page Title | Website Name"

34. `tools_ads`
    - Description: List of advertising tools detected
    - Type: JSON array
    - Example: []

35. `tools_analytics`
    - Description: List of analytics tools detected
    - Type: JSON array
    - Example: ["Google Analytics"]

36. `tools_caching`
    - Description: List of caching tools detected
    - Type: JSON array
    - Example: []

37. `tools_seo`
    - Description: List of SEO tools detected
    - Type: JSON array
    - Example: []

38. `tools_social`
    - Description: List of social media tools detected
    - Type: JSON array
    - Example: []

39. `url_length`
    - Description: Length of the URL
    - Type: Integer
    - Example: 48

40. `viewport`
    - Description: Presence of viewport meta tag
    - Type: Binary (0/1)
    - Example: 1

41. `wordpress`
    - Description: Whether the site uses WordPress
    - Type: Binary (0/1)
    - Example: 0

## Note on Joined Data

When joining these files:
- The `id` column is used as the key for joining
- Duplicate columns (url, main, ip) are removed from the classifier results
- All original columns from results.csv are preserved
- Additional unique columns from classifier_results.csv are added
