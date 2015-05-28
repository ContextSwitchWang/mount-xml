# mount-xml

Mount-xml lets you mount XML-files as read-only file systems.

## Install and run

1. Clone the repository

   ```sh
   $ git clone https://github.com/brisad/mount-xml.git
   $ cd mount-xml
   ```

2. Install dependencies (after optionally activating a virtualenv)

   ```sh
   $ pip install fusepy lxml
   ```

3. Run the command

   ```sh
   $ ./mountxml.py
   usage: ./mountxml.py <xml-file> <mountpoint>
   ```

## Example

A simple XML-file like the following,

```xml
<document>
  <node>
    <subnode>
      Some text
    </subnode>
  </node>
  <node/>
  <last>
    Bye
  </last>
</document>
```

will when mounted look like this:

```sh
$ tree mountpoint/
mountpoint/
|-- #contents
`-- document
    |-- #contents
    |-- last
    |   `-- #contents
    |-- node[1]
    |   |-- #contents
    |   `-- subnode
    |       `-- #contents
    `-- node[2]
        `-- #contents

5 directories, 6 files
```

A `#contents` file contains the tag it is within and all its children:

```sh
$ cat mountpoint/document/node\[1\]/#contents
<node>
    <subnode>
      Some text
    </subnode>
  </node>
```
