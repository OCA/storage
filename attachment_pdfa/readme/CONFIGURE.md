To configure this module:

1. Go to **Settings** > **General Settings**.
2. Scroll down to the **PDF/A Conversion** section under *Document Settings*.
3. Configure your options:
   * **PDF to PDF/A Conversion Method**:
     * **Ghostscript** (default).
     * **Odoo**.
     * **Disable**: Disables automatic conversion globally.
   * **PDF/A Storage Strategy**:
     * **Replace Original File** (default): Overwrites the original PDF attachment with the PDF/A binary.
     * **Store Beside Original File**: Preserves the original file and creates a new attachment named `<Filename>_PDFA.pdf` alongside it.
4. Click **Save**.
