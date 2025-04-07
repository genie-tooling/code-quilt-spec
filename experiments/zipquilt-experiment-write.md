# Understanding the ZIP File Format for Encoding (Creation)

**Goal:** This document describes the structure and process for creating a standard ZIP archive file sequentially.

**Core Concepts:**

1.  **Sequential Writing:** A ZIP file is typically created by writing records sequentially from beginning to end.
2.  **Metadata Accumulation:** Information about each file (like its size, CRC, and where its header was written) needs to be stored temporarily during the creation process to build the Central Directory at the end.
3.  **Signatures (Magic Numbers):** Each record type starts with a unique 4-byte signature.
4.  **Little-Endian:** All multi-byte numerical values are stored in little-endian byte order.
5.  **Data Descriptors (Recommended):** Using Data Descriptors (signaled by setting Bit 3 of the general purpose bit flag) allows writing file data *before* knowing its exact compressed size and CRC. This simplifies streaming creation, as the actual values are written *after* the data.
6.  **Central Directory & EOCD Last:** The Central Directory (listing all files) and the End of Central Directory Record (EOCD) are written *after* all file data has been processed and written.

**Encoding Process Overview:**

1.  **Initialization:** Prepare a list or structure to hold metadata for each file that will eventually go into the Central Directory File Headers (CDFHs).
2.  **Process Each File:** For every file to be added to the archive:
    *   **a. Record LFH Offset:** Get the current position (offset) in the output ZIP file stream. This offset is where the Local File Header (LFH) for this file will begin. Store this offset.
    *   **b. Prepare & Write LFH:** Construct the Local File Header record.
        *   Set signature (`0x04034b50`), version needed, compression method (e.g., 8 for Deflate).
        *   Set file modification time/date.
        *   **Crucially:** Set Bit 3 (0x08) in the general purpose bit flag.
        *   Set CRC-32, compressed size, and uncompressed size fields all to **ZERO** (because Bit 3 is set).
        *   Set filename length (n) and extra field length (m, usually 0).
        *   Write the fixed part of the LFH (30 bytes).
        *   Write the filename (`char[n]`).
        *   Write the extra field (`byte[m]`, if any).
    *   **c. Compress & Write File Data:** Read the input file, compress its data (e.g., using Deflate), and write the resulting compressed bytes directly after the LFH.
        *   While compressing, calculate the CRC-32 checksum of the *original uncompressed* data.
        *   Keep track of the total number of *compressed* bytes written and the total number of *uncompressed* bytes processed.
    *   **d. Write Data Descriptor:** Immediately after the compressed data, write the Data Descriptor record:
        *   Optionally write the signature (`0x08074b50`).
        *   Write the calculated CRC-32 value (4 bytes).
        *   Write the total compressed size (4 bytes).
        *   Write the total uncompressed size (4 bytes).
    *   **e. Store Metadata for CDFH:** Save the relevant information for this file: filename, compression method, time/date, the *actual* CRC-32, *actual* compressed size, *actual* uncompressed size, and the **LFH offset recorded in step 2a**.
3.  **Write Central Directory:** After all input files have been processed and their LFH/Data/Descriptor written:
    *   **a. Record CD Offset:** Get the current position (offset) in the output ZIP file stream. This is where the Central Directory will begin.
    *   **b. Write CDFH Entries:** Iterate through the metadata stored in step 2e for each file. For each file:
        *   Prepare the Central Directory File Header (CDFH) record using the stored metadata.
        *   Set signature (`0x02014b50`), versions, flags (matching LFH, including Bit 3), compression method, time/date.
        *   Set the *actual* CRC-32, compressed size, and uncompressed size.
        *   Set filename length (n), extra field length (m=0), file comment length (k=0).
        *   Set disk number start (0), internal/external attributes.
        *   **Crucially:** Set the `relative offset of local header` to the **LFH offset stored in step 2a**.
        *   Write the fixed part of the CDFH (46 bytes).
        *   Write the filename (`char[n]`).
        *   Write the extra field (`byte[m]`, if any).
        *   Write the file comment (`char[k]`, if any).
    *   **c. Calculate CD Size:** Keep track of the total number of bytes written for all CDFH entries combined. This is the Size of Central Directory.
4.  **Write End of Central Directory (EOCD) Record:** After writing all CDFH entries:
    *   Prepare the EOCD record.
    *   Set signature (`0x06054b50`), disk numbers (all 0), number of CD entries on this disk (equal to total entries), total number of CD entries (total files added).
    *   Set the **Size of Central Directory** (calculated in step 3c).
    *   Set the **Offset of start of Central Directory** (recorded in step 3a).
    *   Set comment length (usually 0 unless adding a global comment).
    *   Write the EOCD record (22 bytes + comment length).
5.  **Finalize:** The ZIP file creation is complete.

---

## Key Record Structures (for Writing)

*(Emphasis on fields calculated/remembered during creation)*

### 1. Local File Header (LFH)

*   **Written:** Before each file's data.
*   **Signature:** `0x04034b50`

| Field                     | Notes for Writing                                                                 |
| :------------------------ | :-------------------------------------------------------------------------------- |
| Version needed            | Set to minimum required (e.g., 20 for Deflate).                                   |
| General purpose bit flag  | **Set Bit 3 (0x08)** to indicate Data Descriptor usage. Set Bit 11 for UTF-8 names? |
| Compression method        | e.g., 0 (Store) or 8 (Deflate).                                                   |
| Time / Date               | Get from source file.                                                             |
| CRC-32                    | **Set to 0** (Actual value goes in Data Descriptor).                              |
| Compressed size           | **Set to 0** (Actual value goes in Data Descriptor).                              |
| Uncompressed size         | **Set to 0** (Actual value goes in Data Descriptor).                              |
| Filename length (n)       | Calculate based on filename bytes.                                                |
| Extra field length (m)    | Usually 0 for simple cases.                                                       |
| **Filename**              | Write `n` bytes after fixed header.                                               |
| **Extra field**           | Write `m` bytes after filename.                                                   |
| *(Compressed Data Follows)* | *(Length determined later, written to Data Descriptor)*                           |

### 2. Data Descriptor (Optional, but Recommended)

*   **Written:** Immediately *after* the compressed file data for a specific file, *if* Bit 3 flag was set in LFH.

| Field                     | Notes for Writing                                              |
| :------------------------ | :------------------------------------------------------------- |
| Data Descriptor Sig?      | *Optional* (`0x08074b50`). Can be omitted for compatibility. |
| CRC-32 checksum           | Write the **actual calculated CRC-32** of uncompressed data.   |
| Compressed size           | Write the **actual measured size** of compressed data written. |
| Uncompressed size         | Write the **actual measured size** of original data processed. |

### 3. Central Directory File Header (CDFH)

*   **Written:** In the Central Directory block *after* all files are processed. One CDFH per file.
*   **Signature:** `0x02014b50`

| Field                          | Notes for Writing                                                                         |
| :----------------------------- | :---------------------------------------------------------------------------------------- |
| Version made by                | Indicate OS/utility (optional detail).                                                    |
| Version needed                 | Match LFH.                                                                                |
| General purpose bit flag       | Match LFH (including Bit 3 set).                                                          |
| Compression method             | Match LFH.                                                                                |
| Time / Date                    | Match LFH (from stored metadata).                                                         |
| CRC-32                         | Use **actual calculated CRC-32** (from stored metadata / Data Descriptor).                |
| Compressed size                | Use **actual measured size** (from stored metadata / Data Descriptor).                    |
| Uncompressed size              | Use **actual measured size** (from stored metadata / Data Descriptor).                    |
| Filename length (n)            | Match LFH (from stored metadata).                                                         |
| Extra field length (m)         | Match LFH (usually 0).                                                                    |
| File comment length (k)        | Usually 0.                                                                                |
| Disk number start              | Set to 0.                                                                                 |
| Internal/External attributes | Set as appropriate (0 or based on source file).                                           |
| **Relative offset local hdr**  | **CRUCIAL:** Use the **LFH offset stored in step 2a**.                                  |
| **Filename**                   | Write `n` bytes (from stored metadata).                                                   |
| **Extra field**                | Write `m` bytes (from stored metadata).                                                   |
| **File comment**               | Write `k` bytes.                                                                          |

### 4. End of Central Directory Record (EOCD)

*   **Written:** Once, at the very end of the file, after the Central Directory.
*   **Signature:** `0x06054b50`

| Field                             | Notes for Writing                                                   |
| :-------------------------------- | :------------------------------------------------------------------ |
| Disk numbers                      | Set to 0.                                                           |
| Num CD entries this disk          | Set to total number of files added.                                 |
| Total num CD entries              | Set to total number of files added.                                 |
| **Size of Central Directory**     | Use the **total size calculated in step 3c**.                     |
| **Offset of start of Central Dir**| Use the **file offset recorded in step 3a**.                      |
| .ZIP file comment length (n)      | Usually 0.                                                          |
| **.ZIP file comment**             | Write `n` bytes if length > 0.                                      |

---

**Summary for LLM:**

To create a ZIP file: for each input file, write a Local Header (LFH) marking sizes/CRC as zero (using bit flag 3), compress and write the data, then write a Data Descriptor with the actual sizes/CRC. Remember the offset where each LFH was written and the final file metadata. After all files are done, write the Central Directory by creating a Central Directory File Header (CDFH) for each file using the remembered metadata (including the LFH offset). Finally, write the End of Central Directory (EOCD) record, providing the location and size of the Central Directory block and the total file count. Remember to write all multi-byte numbers in little-endian format.