

echo "Removing descriptive comments from all files..."

find . -name "*.go" -not -path "./.git/*" | while read -r file; do
    echo "Processing Go file: $file"
    sed -i '/^[[:space:]]*\/\/.*$/d' "$file"
done

find . -name "*.py" -not -path "./.git/*" | while read -r file; do
    echo "Processing Python file: $file"
    sed -i '/^[[:space:]]*#.*$/d' "$file"
done

find . -name "*.sh" -not -path "./.git/*" | while read -r file; do
    echo "Processing shell script: $file"
    sed -i '/^[[:space:]]*#.*$/d' "$file"
done

find . -name "*.yml" -o -name "*.yaml" -not -path "./.git/*" | while read -r file; do
    echo "Processing YAML file: $file"
    sed -i '/^[[:space:]]*#.*$/d' "$file"
done

find . -name "Dockerfile*" -not -path "./.git/*" | while read -r file; do
    echo "Processing Dockerfile: $file"
    sed -i '/^[[:space:]]*#.*$/d' "$file"
done

find . -name "*.sql" -not -path "./.git/*" | while read -r file; do
    echo "Processing SQL file: $file"
    sed -i '/^[[:space:]]*--.*$/d' "$file"
done

echo "Comment removal completed!"
