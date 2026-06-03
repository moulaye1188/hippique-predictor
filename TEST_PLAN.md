# Test Plan - Progressive Learning Horse Racing Prediction System

## Pre-Test Checklist
- [ ] Docker container is running (port 5000)
- [ ] Database is initialized
- [ ] Model is loaded
- [ ] Frontend loads at http://localhost:5000

## Test Scenario 1: Basic Prediction (Existing Functionality)
1. Navigate to "📊 Prédiction" tab
2. Fill in race information (date, hippodrome, distance, type)
3. Ensure at least 3 horses in the table
4. Click "🔮 Générer Pronostic"
5. **Expected**: Results display with predictions, chart, and confidence scores
6. **Verify**: 
   - Results sorted by probability (descending)
   - Probabilities sum to ~100%
   - Chart displays correctly
   - Status shows success message

## Test Scenario 2: Data Import
1. Prepare a test CSV file with horse race data:
   ```csv
   horse_number,horse_name,description,odds,result_position
   1,HORSE_A,Strong performer,10/1,1
   2,HORSE_B,Average,20/1,2
   3,HORSE_C,Weak,50/1,3
   ```
2. Navigate to "📤 Import" tab
3. Select the CSV file
4. Click "📥 Importer Fichier"
5. **Expected**: 
   - Success message shows imported count
   - Preview table displays imported data
   - "Courses Importées" shows count > 0
6. **Verify**: Data is stored in database

## Test Scenario 3: Correlation Analysis
1. Click "🔍 Analyse" tab
2. Click "🔄 Lancer Analyse"
3. **Expected**: 
   - Success message appears
   - Top 10 factors displayed with:
     - Rank number
     - Feature name
     - Correlation value (-1 to 1)
     - Strength classification (Very Strong, Strong, etc.)
     - Direction (positive/negative)
   - Feature groups section shows categorized factors
4. **Verify**: 
   - Factors are ranked by strength
   - Correlations make sense (between -1 and 1)

## Test Scenario 4: Feedback Submission
1. Make a prediction in "📊 Prédiction" tab (save the race_id)
2. Click on "✓ Feedback" tab
3. Fill in feedback form:
   - Race ID: (use the ID from prediction)
   - Horse ID: 1
   - Predicted Rank: 1 (if you predicted winner)
   - Position Réelle: 1 (actual winner)
4. Click "✓ Soumettre Feedback"
5. **Expected**: 
   - "Feedback enregistré!" success message
   - Form clears
   - Status indicates model is retraining if >= 10 feedback records
6. **Verify**: 
   - Data saved to prediction_feedback table
   - Prediction marked as correct if actual_position matches predicted

## Test Scenario 5: Dashboard Performance
1. Navigate to "📈 Dashboard" tab
2. Click "🔄 Rafraîchir Dashboard"
3. **Expected**: 
   - Metrics cards display:
     - Précision Globale (%)
     - Total Prédictions (count)
     - Correctes (count)
     - Tendance (improving/stable/declining)
   - Accuracy timeline chart displays
   - Top factors table shows best predictive features
   - Recommendations list shows guidance
4. **Verify**: 
   - Accuracy = (correct / total) * 100
   - Chart shows trend over races
   - Recommendations are contextual

## Test Scenario 6: Manual Retraining
1. In "📈 Dashboard" tab
2. Click "🤖 Réentraîner Modèle"
3. Confirm the retraining dialog
4. **Expected**: 
   - "Réentraînement en cours..." loading message
   - After completion: "✅ Réentraînement complété! Accuracy: X%"
   - Dashboard auto-refreshes with updated metrics
5. **Verify**: 
   - Model file updated (/app/models/race_prediction_model.h5)
   - New metrics recorded in database
   - Dashboard shows updated values

## Test Scenario 7: Progressive Learning Workflow
1. **Step 1**: Import historical data
   - 📤 Import tab → CSV with 100+ races
   - Verify import successful
   
2. **Step 2**: Analyze correlations
   - 🔍 Analyse tab → Identify best factors
   - Note top 5 factors
   
3. **Step 3**: Make predictions
   - 📊 Prédiction tab → Create prediction
   - Save race_id for feedback
   
4. **Step 4**: Submit feedback (5-10 times)
   - ✓ Feedback tab → Submit actual results
   - Each time, note if prediction was correct
   
5. **Step 5**: Check improving accuracy
   - 📈 Dashboard tab
   - Verify accuracy trend is "improving"
   - Should see accuracy increase from initial to final predictions
   
6. **Step 6**: Re-analyze correlations
   - 🔍 Analyse tab → Re-run analysis
   - Compare with Step 2
   - Different factors may now be important
   
7. **Expected**: 
   - Accuracy improves from baseline to final
   - Factor importance may shift
   - Dashboard shows positive trend

## Test Scenario 8: Error Handling
1. **Invalid file upload**: Try importing a .txt file with invalid format
   - **Expected**: Error message displayed, import fails gracefully
   
2. **Missing feedback fields**: Try submitting feedback without race_id
   - **Expected**: Alert "Veuillez remplir tous les champs obligatoires"
   
3. **No historical data for analysis**: Try analyzing before importing data
   - **Expected**: Error message "No historical data available for analysis"
   
4. **Insufficient data for retraining**: Try retraining with < 10 samples
   - **Expected**: Error "Not enough data for retraining"

## Test Scenario 9: UI Responsiveness
1. Test on mobile (simulate 480px width)
   - [ ] All tabs visible and accessible
   - [ ] Forms stack vertically
   - [ ] Tables scroll horizontally
   - [ ] Buttons are clickable
   
2. Test on tablet (768px width)
   - [ ] Layout adjusts properly
   - [ ] Charts display correctly
   
3. Test on desktop (1200px+)
   - [ ] Multi-column layouts render
   - [ ] Metrics grid displays side-by-side

## Test Scenario 10: API Direct Testing (curl)
```bash
# Health check
curl http://localhost:5000/api/health

# Get races history
curl http://localhost:5000/api/races?limit=10

# Get dashboard data
curl http://localhost:5000/api/dashboard

# Get correlations
curl http://localhost:5000/api/analyze
```

## Success Criteria
- ✅ All 7 tabs functional and responsive
- ✅ Data import works with CSV/PDF
- ✅ Correlation analysis identifies factors
- ✅ Feedback submission triggers retraining
- ✅ Dashboard shows improving accuracy trend
- ✅ Manual retraining updates metrics
- ✅ No JavaScript errors in browser console
- ✅ No Python errors in container logs
- ✅ UI responsive across device sizes
- ✅ All error cases handled gracefully

## Debug Tips
- View container logs: `docker compose logs app -f`
- Check database: `sqlite3 data/hippique.db`
- Browser console (F12) for JavaScript errors
- Network tab for API response status
- Check model file exists: `ls -la models/`
