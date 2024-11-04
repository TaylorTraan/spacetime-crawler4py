# Read from the report.txt file, process the data, and write to report2.txt
def process_report(file_in='report.txt', file_out='report2.txt'):
    # Dictionary to store subdomains and the count of unique pages
    subdomain_counts = {}

    # Read the file line by line
    with open(file_in, 'r') as file:
        for line in file:
            # Split the line by ":" to separate subdomain and pages
            if ':' in line:
                subdomain, pages = line.split(":", 1)
                try:
                    # Convert the pages part to a set to get unique page count
                    unique_pages = eval(pages.strip())
                    
                    # Ensure unique_pages is a set before proceeding
                    if isinstance(unique_pages, set):
                        subdomain_counts[subdomain.strip()] = len(unique_pages)
                    else:
                        print(f"Skipping line with unexpected format: {line.strip()}")
                
                except Exception as e:
                    print(f"Error processing line: {line.strip()} - {e}")
                    continue

    # Sort the subdomains alphabetically
    sorted_subdomains = sorted(subdomain_counts.items())

    # Write the results to the new file
    with open(file_out, 'w') as file:
        for subdomain, count in sorted_subdomains:
            file.write(f"{subdomain}: {count}\n")

    print(f"Report generated: {file_out}")

if __name__ == '__main__':
    process_report()
