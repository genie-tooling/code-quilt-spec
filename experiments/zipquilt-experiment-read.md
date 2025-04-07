# Understanding the ZIP File Format for Decoding

**Goal:** This document describes the structure of a standard ZIP archive file to enable understanding of the decoding (reading/extraction) process.

**Core Concepts:**

1.  **Sequential Records:** A ZIP file is composed of several data records laid out sequentially.
2.  **Signatures (Magic Numbers):** Each record type starts with a unique 4-byte signature for identification.
3.  **Little-Endian:** All multi-byte numerical values (e.g., uint16_t, uint32_t) are stored in little-endian byte order unless otherwise specified.
4.  **Central Directory:** A core structure located near the *end* of the file that acts as a table of contents, listing metadata for *all* files in the archive and pointing to their actual data.
5.  **Local File Headers:** Metadata records located *immediately before* each file's compressed data.
6.  **End of Central Directory Record (EOCD):** The *very last* record in the ZIP file (excluding the optional comment). It's crucial for locating the Central Directory.

**Decoding Process Overview:**

1.  **Find the EOCD Record:** Scan backwards from the end of the file searching for the EOCD signature (0x06054b50).
2.  **Parse EOCD:** Extract information, primarily the offset (location) and size of the Central Directory.
3.  **Seek & Read Central Directory:** Jump to the specified offset and read the entire Central Directory block.
4.  **Parse Central Directory Entries:** Iterate through the Central Directory block, parsing each Central Directory File Header (CDFH) record.
5.  **For Each CDFH Entry:**
    *   Extract file metadata (filename, compression method, CRC-32, sizes, etc.).
    *   Crucially, get the `relative offset of local header`. This tells you where the corresponding Local File Header (and thus the file data) starts within the ZIP file.
6.  **Extract Individual File:**
    *   Seek to the `relative offset of local header` obtained from the CDFH.
    *   Parse the Local File Header (LFH) record found there. (Often contains redundant info from CDFH).
    *   The compressed file data immediately follows the LFH (after its variable-length filename and extra field).
    *   Read the `compressed size` number of bytes.
    *   Decompress the data using the specified `compression method`.
    *   Verify the `uncompressed size` and `CRC-32` checksum against the metadata from CDFH/LFH.
    *   Handle optional Data Descriptors if indicated by the LFH's general purpose bit flag.

---

## Key Record Structures (for Reading)

*(Offsets are relative to the start of the specific record)*

### 1. End of Central Directory Record (EOCD)

*   **Found:** At the very end of the file (before the ZIP file comment). Scan backwards for the signature.
*   **Signature:** `0x06054b50` (4 bytes)

| Offset | Size (bytes) | Data Type    | Description                                      | Notes                                                              |
| :----- | :----------- | :----------- | :----------------------------------------------- | :----------------------------------------------------------------- |
| 0      | 4            | `uint32_t`   | EOCD Signature (`0x06054b50`)                    |                                                                    |
| 4      | 2            | `uint16_t`   | Number of this disk                              | Usually 0 for single-file archives.                                |
| 6      | 2            | `uint16_t`   | Disk where Central Directory starts              | Usually 0.                                                         |
| 8      | 2            | `uint16_t`   | Number of Central Directory entries on this disk | Total entries if not spanning disks.                               |
| 10     | 2            | `uint16_t`   | Total number of Central Directory entries        | **Important:** Total file count.                                   |
| 12     | 4            | `uint32_t`   | Size of Central Directory                        | **Important:** Size in bytes.                                      |
| 16     | 4            | `uint32_t`   | Offset of start of Central Directory             | **Important:** File offset from start of *first* disk (usually 0). |
| 20     | 2            | `uint16_t`   | `.ZIP` file comment length (n)                   |                                                                    |
| 22     | n            | `char[n]`    | `.ZIP` file comment                            | Optional comment follows immediately.                              |

### 2. Central Directory File Header (CDFH)

*   **Found:** Sequentially within the Central Directory block located via EOCD. Repeat for each file entry.
*   **Signature:** `0x02014b50` (4 bytes)

| Offset | Size (bytes) | Data Type    | Description                                      | Notes                                                            |
| :----- | :----------- | :----------- | :----------------------------------------------- | :--------------------------------------------------------------- |
| 0      | 4            | `uint32_t`   | CDFH Signature (`0x02014b50`)                    |                                                                  |
| 4      | 2            | `uint16_t`   | Version made by                                  | Host OS / ZIP utility info.                                      |
| 6      | 2            | `uint16_t`   | Version needed to extract                      | Minimum ZIP spec version.                                        |
| 8      | 2            | `uint16_t`   | General purpose bit flag                       | **Bit 3 (0x08):** If set, sizes/CRC are zero, use Data Descriptor. |
| 10     | 2            | `uint16_t`   | Compression method                             | **0=Stored**, **8=Deflated**. Others exist.                      |
| 12     | 2            | `uint16_t`   | File last modification time                    | MS-DOS format.                                                   |
| 14     | 2            | `uint16_t`   | File last modification date                    | MS-DOS format.                                                   |
| 16     | 4            | `uint32_t`   | CRC-32 checksum                                | Of uncompressed data. (Unless Bit 3 flag set).                   |
| 20     | 4            | `uint32_t`   | Compressed size                                | Size of file data in bytes. (Unless Bit 3 flag set).             |
| 24     | 4            | `uint32_t`   | Uncompressed size                              | Original file size. (Unless Bit 3 flag set).                   |
| 28     | 2            | `uint16_t`   | Filename length (n)                            |                                                                  |
| 30     | 2            | `uint16_t`   | Extra field length (m)                         |                                                                  |
| 32     | 2            | `uint16_t`   | File comment length (k)                        |                                                                  |
| 34     | 2            | `uint16_t`   | Disk number where file starts                    | Usually 0.                                                       |
| 36     | 2            | `uint16_t`   | Internal file attributes                       | Usage varies.                                                    |
| 38     | 4            | `uint32_t`   | External file attributes                       | Host OS-specific permissions/attributes.                         |
| 42     | 4            | `uint32_t`   | **Relative offset of local header**            | **CRUCIAL:** File offset of the corresponding LFH record.         |
| 46     | n            | `char[n]`    | Filename                                         | Not null-terminated. Use filename length. Encoding varies (often CP437 or UTF-8 if bit 11 flag set). |
| 46+n   | m            | `byte[m]`    | Extra field                                      | Optional structured data (e.g., Zip64 info, timestamps).           |
| 46+n+m | k            | `char[k]`    | File comment                                     | Optional per-file comment.                                     |

### 3. Local File Header (LFH)

*   **Found:** Immediately before each file's data stream, at the offset specified by the corresponding CDFH.
*   **Signature:** `0x04034b50` (4 bytes)
*   **Note:** Many fields are duplicated from the CDFH. For reading, the CDFH is often considered the authoritative source.

| Offset | Size (bytes) | Data Type    | Description                  | Notes                                                          |
| :----- | :----------- | :----------- | :--------------------------- | :------------------------------------------------------------- |
| 0      | 4            | `uint32_t`   | LFH Signature (`0x04034b50`) |                                                                |
| 4      | 2            | `uint16_t`   | Version needed to extract  | Minimum ZIP spec version.                                      |
| 6      | 2            | `uint16_t`   | General purpose bit flag   | **Bit 3 (0x08):** If set, use Data Descriptor after file data. |
| 8      | 2            | `uint16_t`   | Compression method         | **0=Stored**, **8=Deflated**. Must match CDFH.                 |
| 10     | 2            | `uint16_t`   | File last modification time |                                                                |
| 12     | 2            | `uint16_t`   | File last modification date |                                                                |
| 14     | 4            | `uint32_t`   | CRC-32 checksum            | (Unless Bit 3 flag set). Should match CDFH.                  |
| 18     | 4            | `uint32_t`   | Compressed size            | (Unless Bit 3 flag set). Should match CDFH.                  |
| 22     | 4            | `uint32_t`   | Uncompressed size          | (Unless Bit 3 flag set). Should match CDFH.                  |
| 26     | 2            | `uint16_t`   | Filename length (n)        | Should match CDFH.                                             |
| 28     | 2            | `uint16_t`   | Extra field length (m)     | Should match CDFH.                                             |
| 30     | n            | `char[n]`    | Filename                   | Immediately follows header.                                    |
| 30+n   | m            | `byte[m]`    | Extra field                | Immediately follows filename.                                  |
| **30+n+m** | **CompSize** | `byte[]`   | **Compressed File Data**   | **Starts HERE.** Read `Compressed size` bytes.             |

### 4. Data Descriptor (Optional)

*   **Found:** Immediately *after* the compressed file data, **only if** Bit 3 (0x08) of the general purpose bit flag is set in the LFH/CDFH.
*   **Signature:** `0x08074b50` (4 bytes) - **Note:** This signature is *optional* according to the spec and might not be present. Reliable parsers often check for it but must be prepared if it's absent.

| Offset | Size (bytes) | Data Type    | Description          | Notes                           |
| :----- | :----------- | :----------- | :------------------- | :------------------------------ |
| 0      | 4            | `uint32_t`   | Data Descriptor Sig? | *Optional* (`0x08074b50`)     |
| 0 or 4 | 4            | `uint32_t`   | CRC-32 checksum      | The *actual* CRC-32 value.    |
| 4 or 8 | 4            | `uint32_t`   | Compressed size      | The *actual* compressed size. |
| 8 or 12| 4            | `uint32_t`   | Uncompressed size    | The *actual* uncompressed size. |

---

**Summary for LLM:**

To read a ZIP file: find the EOCD at the end, use it to find the Central Directory, read the Central Directory to get a list of files and pointers (offsets) to their Local File Headers, jump to each Local File Header, read the compressed data that follows it, and decompress. Use the signatures to identify records and parse the fields according to their specified size and little-endian format. Pay attention to the general purpose bit flag (Bit 3) to know if size/CRC information is delayed until after the file data in a Data Descriptor.