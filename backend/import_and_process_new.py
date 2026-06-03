def import_and_process(file_path: str, file_type: str = 'auto') -> Tuple[pd.DataFrame, List[str]]:
    """
    Main function to import and process race data
    
    Returns:
        Tuple of (processed_dataframe, list_of_errors)
    """
    importer = DataImporter()
    errors = []
    df = None
    
    try:
        if file_type == 'csv' or (file_type == 'auto' and file_path.endswith('.csv')):
            df = importer.import_csv(file_path)
        
        elif file_type == 'pdf' or (file_type == 'auto' and file_path.endswith('.pdf')):
            # Use new pdfplumber parser first
            try:
                from pdf_integration import parse_pdf_file
                race_info, df = parse_pdf_file(file_path)
                
                # Add race info to dataframe as columns
                if df is not None and not df.empty and race_info:
                    for key, val in race_info.items():
                        df[key] = val
            except Exception as e:
                print(f"Error with new PDF parser: {e}")
                df = None
            
            # Fallback to old parser if new one fails
            if df is None or df.empty:
                print("Falling back to old PDF parser")
                text = importer.import_pdf_text(file_path)
                df = importer.parse_text_data(text)
        
        elif file_type == 'text':
            # File_path is actually text content
            df = importer.parse_text_data(file_path)
        
        else:
            # Try auto-detect based on content
            df = importer.parse_text_data(file_path)
        
        if df is None or df.empty:
            return None, ["No data could be extracted"]
        
        # Clean and extract features
        df = importer._clean_dataframe(df)
        df = importer.extract_features(df)
        df = OddsFeatureExtractor.extract_odds_features(df)
        
        # Validate
        is_valid, validation_errors = importer.validate_data(df)
        if not is_valid:
            errors.extend(validation_errors)
        
        return df, errors
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, [str(e)]
