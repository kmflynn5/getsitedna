# GetSiteDNA CLI Examples

This document provides comprehensive examples of using the GetSiteDNA command-line interface.

## Basic Analysis

### Simple Analysis
```bash
# Analyze a website with default settings
getsitedna analyze https://example.com

# Output will be saved to ./analysis/ directory
```

### Custom Output Directory
```bash
# Specify custom output directory
getsitedna analyze https://example.com --output ./my-website-analysis

# Use short form
getsitedna analyze https://example.com -o ./results
```

### Depth and Page Limits
```bash
# Limit crawling depth to 3 levels
getsitedna analyze https://example.com --depth 3

# Limit to maximum 100 pages
getsitedna analyze https://example.com --max-pages 100

# Combine both options
getsitedna analyze https://example.com -d 2 -p 50
```

## Advanced Analysis Options

### Browser Selection
```bash
# Use Firefox for JavaScript rendering
getsitedna analyze https://spa-example.com --browser firefox

# Use WebKit engine
getsitedna analyze https://example.com --browser webkit

# Default is Chromium
getsitedna analyze https://example.com --browser chromium
```

### Asset Handling
```bash
# Include asset extraction (default)
getsitedna analyze https://example.com --include-assets

# Skip asset extraction for faster analysis
getsitedna analyze https://example.com --no-assets
```

### Interactive Mode
```bash
# Run in interactive mode with guided prompts
getsitedna analyze https://example.com --interactive

# Interactive mode will ask for:
# - Analysis philosophy
# - Target framework
# - Accessibility level
# - Asset preferences
# - Performance settings
```

## Complete Analysis Examples

### E-commerce Site Analysis
```bash
# Comprehensive analysis for e-commerce site
getsitedna analyze https://shop.example.com \
  --depth 4 \
  --max-pages 200 \
  --include-assets \
  --browser chromium \
  --output ./ecommerce-analysis
```

### Landing Page Analysis
```bash
# Quick analysis for a landing page
getsitedna analyze https://landing.example.com \
  --depth 1 \
  --max-pages 5 \
  --no-assets \
  --output ./landing-analysis
```

### SPA (Single Page Application) Analysis
```bash
# Analysis for JavaScript-heavy SPA
getsitedna analyze https://app.example.com \
  --depth 2 \
  --max-pages 50 \
  --browser firefox \
  --include-assets \
  --output ./spa-analysis
```

## Performance Management

### Check Performance Status
```bash
# View current performance settings and cache status
getsitedna performance status
```

### Configure Performance Settings
```bash
# Set maximum concurrent workers
getsitedna performance configure --workers 8

# Set batch processing size
getsitedna performance configure --batch-size 10

# Set memory threshold (percentage)
getsitedna performance configure --memory-threshold 75

# Combine multiple settings
getsitedna performance configure \
  --workers 6 \
  --batch-size 8 \
  --memory-threshold 80 \
  --cpu-threshold 85
```

### Enable/Disable Features
```bash
# Enable caching
getsitedna performance configure --enable-caching

# Disable caching
getsitedna performance configure --disable-caching

# Enable performance monitoring
getsitedna performance configure --enable-monitoring

# Disable performance monitoring
getsitedna performance configure --disable-monitoring
```

### Cache Management
```bash
# Configure cache settings
getsitedna performance cache-config --ttl 7200  # 2 hours
getsitedna performance cache-config --max-size 200  # 200MB
getsitedna performance cache-config --cache-dir ~/.getsitedna/cache

# Clear all cached data
getsitedna performance clear-cache

# Reset performance settings to defaults
getsitedna performance reset
```

### Performance Benchmarking
```bash
# Run performance benchmark
getsitedna performance benchmark

# This will show:
# - Execution time
# - Memory usage
# - CPU usage
# - Concurrent task performance
```

### Export/Import Configuration
```bash
# Export current configuration
getsitedna performance export-config --output my-config.json

# Import configuration from file
getsitedna performance import-config my-config.json
```

## Validation and Quality Assurance

### Validate Analysis Results
```bash
# Validate analysis output structure
getsitedna validate-analysis ./analysis

# Validate with detailed output
getsitedna validate-analysis ./analysis --output validation-report.json
```

## Real-World Workflows

### Complete Website Audit
```bash
#!/bin/bash
# complete-audit.sh - Comprehensive website audit

WEBSITE="https://example.com"
OUTPUT_DIR="./audit-$(date +%Y%m%d)"

echo "🔍 Starting complete audit of $WEBSITE"

# Configure performance for comprehensive analysis
getsitedna performance configure \
  --workers 4 \
  --batch-size 5 \
  --enable-caching \
  --enable-monitoring

# Run comprehensive analysis
getsitedna analyze $WEBSITE \
  --interactive \
  --depth 3 \
  --max-pages 100 \
  --include-assets \
  --output $OUTPUT_DIR

# Validate results
getsitedna validate-analysis $OUTPUT_DIR

# Show cache statistics
getsitedna performance status

echo "✅ Audit complete! Results in $OUTPUT_DIR"
```

### Competitive Analysis Batch
```bash
#!/bin/bash
# competitive-analysis.sh - Analyze multiple competitor sites

COMPETITORS=(
  "https://competitor1.com"
  "https://competitor2.com"
  "https://competitor3.com"
)

# Configure for fast batch processing
getsitedna performance configure \
  --workers 6 \
  --batch-size 3 \
  --disable-monitoring

for site in "${COMPETITORS[@]}"; do
  domain=$(echo $site | sed 's|https\?://||' | sed 's|/.*||')
  echo "🔍 Analyzing $domain..."
  
  getsitedna analyze $site \
    --depth 2 \
    --max-pages 20 \
    --no-assets \
    --output "./competitors/$domain"
done

echo "✅ Competitive analysis complete!"
```

### Design System Extraction
```bash
#!/bin/bash
# extract-design-system.sh - Focus on design system extraction

WEBSITE="https://designsystem.example.com"

echo "🎨 Extracting design system from $WEBSITE"

# Configure for design-focused analysis
getsitedna performance configure \
  --workers 2 \
  --enable-caching

# Run design-focused analysis
getsitedna analyze $WEBSITE \
  --depth 2 \
  --max-pages 30 \
  --include-assets \
  --browser chromium \
  --output ./design-system

# The analysis will generate:
# - Color palette extraction
# - Typography analysis
# - Component identification
# - Design token specifications

echo "✅ Design system extraction complete!"
echo "📁 Check ./design-system/DESIGN_SYSTEM.md for results"
```

### Performance Monitoring Workflow
```bash
#!/bin/bash
# performance-monitoring.sh - Monitor analysis performance

echo "📊 Performance Monitoring Workflow"

# Enable detailed monitoring
getsitedna performance configure \
  --enable-monitoring \
  --workers 4

# Run benchmark
echo "🏃 Running baseline benchmark..."
getsitedna performance benchmark

# Run actual analysis with monitoring
echo "🔍 Running monitored analysis..."
getsitedna analyze https://example.com \
  --depth 2 \
  --max-pages 25 \
  --output ./monitored-analysis

# Check final performance status
echo "📈 Final performance status:"
getsitedna performance status
```

## Environment Configuration

### Using Environment Variables
```bash
# Set cache configuration
export GETSITEDNA_CACHE_ENABLED=true
export GETSITEDNA_CACHE_TTL=3600
export GETSITEDNA_CACHE_MAX_SIZE=104857600  # 100MB

# Set performance configuration
export GETSITEDNA_MAX_WORKERS=6
export GETSITEDNA_BATCH_SIZE=8

# Enable debug mode
export GETSITEDNA_DEBUG_MODE=true

# Run analysis with environment configuration
getsitedna analyze https://example.com
```

### Configuration File Setup
```bash
# Create default configuration
getsitedna config init

# This creates ~/.getsitedna/config.json with default settings
# Edit the file to customize your default settings
```

## Troubleshooting Commands

### Debug Mode
```bash
# Enable debug mode for verbose output
export GETSITEDNA_DEBUG_MODE=true
getsitedna analyze https://problematic-site.com

# Check cache for issues
getsitedna performance status

# Clear cache if needed
getsitedna performance clear-cache
```

### Performance Issues
```bash
# If analysis is slow, try:
getsitedna performance configure --workers 2 --batch-size 3

# If memory issues occur:
getsitedna performance configure --memory-threshold 60

# For timeout issues:
getsitedna analyze https://slow-site.com --depth 1 --max-pages 10
```

### Network Issues
```bash
# For sites with rate limiting:
getsitedna performance configure --workers 1

# Skip assets if connection is slow:
getsitedna analyze https://example.com --no-assets

# Use static crawler only:
getsitedna analyze https://example.com --browser none  # (if implemented)
```

## Tips and Best Practices

### Optimal Settings for Different Site Types

**Large E-commerce Sites:**
```bash
getsitedna analyze https://shop.com --depth 3 --max-pages 150 --workers 4
```

**Marketing Landing Pages:**
```bash
getsitedna analyze https://landing.com --depth 1 --max-pages 5 --no-assets
```

**Corporate Websites:**
```bash
getsitedna analyze https://corporate.com --depth 2 --max-pages 50 --include-assets
```

**Single Page Applications:**
```bash
getsitedna analyze https://spa.com --depth 2 --browser chromium --include-assets
```

### Performance Optimization
1. Use caching for repeated analyses
2. Adjust worker count based on your system
3. Use `--no-assets` for faster initial analysis
4. Start with shallow depth, increase as needed
5. Monitor memory usage with large sites

### Quality Assurance
1. Always validate analysis results
2. Check for warnings in the output
3. Review generated documentation
4. Test with different browser engines if issues occur