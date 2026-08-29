# Pins the exact Jekyll/Liquid versions GitHub Pages runs, so a local build is a
# real test rather than an approximation.
#
#   bundle install                              # once
#   bundle exec jekyll build --destination /tmp/pbtest
#   bundle exec jekyll serve                    # preview at localhost:4000
#
# Why this matters: a plain `gem install jekyll` gets Jekyll 4.x, whose newer
# Liquid accepts syntax that GitHub's Liquid 4.0.4 rejects. A compound
# `where_exp` condition built fine locally on Jekyll 4 and failed the Pages
# build. Always verify through bundler, not the bare `jekyll` binary.

source "https://rubygems.org"

gem "github-pages", group: :jekyll_plugins

# Ruby 3.4+ removed these from the default gems, and the Jekyll version GitHub
# Pages runs still expects them. Without these the local build dies with
# "cannot load such file -- csv" before it ever reaches your content.
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"
gem "ostruct"
gem "webrick"
