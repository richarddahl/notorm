# Attributes and Values CLI Tools

This document provides documentation for the command-line interface (CLI) tools for managing attributes and values.

## Attributes CLI Tool

The attributes CLI tool provides commands for managing attribute types and attribute instances.

### Installation

The tool is installed as part of the main package and is available as `attributes_cli.py` in the `src/scripts` directory.

### Usage

```bash
python src/scripts/attributes_cli.py [command] [subcommand] [options]
```

### Commands

#### Attribute Types

##### Create an attribute type
```bash
python src/scripts/attributes_cli.py attribute-types create \
  --name "Priority" \
  --text "What is the priority of this item?" \
  --required \
  --multiple-allowed \
  --display-with-objects \
  --meta-type-ids 01H3ZEVKY6ZH3F41K5GS77PJ1Z \
  --value-type-ids 01H3ZEVKY9PDSF51K5HS77PJ2A
```

##### Get an attribute type by ID
```bash
python src/scripts/attributes_cli.py attribute-types get 01H3ZEVKXN7PQWGW5KVS77PJ0Y
```

##### List attribute types
```bash
# List all attribute types
python src/scripts/attributes_cli.py attribute-types list

# List attribute types applicable to a meta type
python src/scripts/attributes_cli.py attribute-types list --meta-type-id 01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

##### Delete an attribute type
```bash
python src/scripts/attributes_cli.py attribute-types delete 01H3ZEVKXN7PQWGW5KVS77PJ0Y
```

#### Attributes

##### Create an attribute
```bash
python src/scripts/attributes_cli.py attributes create \
  --attribute-type-id 01H3ZEVKXN7PQWGW5KVS77PJ0Y \
  --comment "This is a test attribute" \
  --follow-up-required \
  --value-ids 01H3ZEVKY6ZH3F41K5GS77PJ1Z 01H3ZEVKY9PDSF51K5HS77PJ2A
```

##### Get an attribute by ID
```bash
python src/scripts/attributes_cli.py attributes get 01H3ZEVKXN7PQWGW5KVS77PJ0Y
```

##### Add values to an attribute
```bash
python src/scripts/attributes_cli.py attributes add-values 01H3ZEVKXN7PQWGW5KVS77PJ0Y 01H3ZEVKY6ZH3F41K5GS77PJ1Z 01H3ZEVKY9PDSF51K5HS77PJ2A
```

##### Remove values from an attribute
```bash
python src/scripts/attributes_cli.py attributes remove-values 01H3ZEVKXN7PQWGW5KVS77PJ0Y 01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

##### Get attributes for a record
```bash
# Get attributes for a record including values
python src/scripts/attributes_cli.py attributes get-for-record 01H3ZEVKY6ZH3F41K5GS77PJ1Z

# Get attributes for a record without values
python src/scripts/attributes_cli.py attributes get-for-record 01H3ZEVKY6ZH3F41K5GS77PJ1Z --no-values
```

##### Delete an attribute
```bash
python src/scripts/attributes_cli.py attributes delete 01H3ZEVKXN7PQWGW5KVS77PJ0Y
```

## Values CLI Tool

The values CLI tool provides commands for managing different types of values.

### Installation

The tool is installed as part of the main package and is available as `values_cli.py` in the `src/scripts` directory.

### Usage

```bash
python src/scripts/values_cli.py [command] [options]
```

### Commands

#### Create a value
```bash
# Create a boolean value
python src/scripts/values_cli.py create --value-type boolean --value true --name "Boolean Example"

# Create an integer value
python src/scripts/values_cli.py create --value-type integer --value 42 --name "Integer Example"

# Create a text value
python src/scripts/values_cli.py create --value-type text --value "Example text" --name "Text Example"

# Create a decimal value
python src/scripts/values_cli.py create --value-type decimal --value 3.14159 --name "Decimal Example"

# Create a date value
python src/scripts/values_cli.py create --value-type date --value "2023-01-15" --name "Date Example"

# Create a datetime value
python src/scripts/values_cli.py create --value-type datetime --value "2023-01-15T14:30:15" --name "DateTime Example"

# Create a time value
python src/scripts/values_cli.py create --value-type time --value "14:30:15" --name "Time Example"
```

#### Get or create a value
```bash
# Get or create a text value
python src/scripts/values_cli.py get-or-create --value-type text --value "Example text" --name "Text Example"
```

#### Get a value by ID
```bash
# Get a text value by ID
python src/scripts/values_cli.py get --value-type text --id 01H3ZEVKY6ZH3F41K5GS77PJ1Z

# Get an attachment by ID
python src/scripts/values_cli.py get --value-type attachment --id 01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

#### Convert a value to a different type
```bash
# Convert a text value to a boolean
python src/scripts/values_cli.py convert --source-type text --target-type boolean --value "true"

# Convert an integer to a decimal
python src/scripts/values_cli.py convert --source-type integer --target-type decimal --value 42
```

#### Upload a file attachment
```bash
python src/scripts/values_cli.py upload --file-path /path/to/file.pdf --name "Example PDF"
```

#### Delete a value
```bash
# Delete a text value
python src/scripts/values_cli.py delete --value-type text --id 01H3ZEVKY6ZH3F41K5GS77PJ1Z

# Delete an attachment
python src/scripts/values_cli.py delete --value-type attachment --id 01H3ZEVKY6ZH3F41K5GS77PJ1Z
```

#### Search for values
```bash
# Search for text values
python src/scripts/values_cli.py search --value-type text --term "example" --limit 10

# Search for attachments
python src/scripts/values_cli.py search --value-type attachment --term "pdf" --limit 10
```

## Integrating with Other Tools

Both CLI tools can be integrated with other scripts and tools using standard Unix pipelines. For example:

```bash
# Get attribute type IDs and pipe to another command
python src/scripts/attributes_cli.py attribute-types list | grep -o "ID: [A-Z0-9]\+" | cut -d" " -f2 > attribute_type_ids.txt

# Use the attributes CLI in a loop
for id in $(cat attribute_type_ids.txt); do
  python src/scripts/attributes_cli.py attribute-types get $id
done

# Pipe output to jq for JSON processing
python src/scripts/values_cli.py get --value-type text --id 01H3ZEVKY6ZH3F41K5GS77PJ1Z | jq '.value'
```