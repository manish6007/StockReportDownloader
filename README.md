# Company Analysis Tool

A Streamlit-based web application for analyzing stock data and generating reports. This tool executes analysis scripts and organizes the generated reports in a user-specified directory structure.

## Features

- Web-based interface for stock analysis
- Automated report generation
- Custom target directory selection for report storage
- Organized folder structure (one folder per stock symbol)
- Real-time progress tracking
- Detailed execution logs
- Error handling and validation

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application expects the following analysis scripts in the same directory:
- `crawl_screener_generate_report_in_folder.py`
- `download_candledata_in_folder.py`

Make sure these scripts are present and have the correct permissions.

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Access the web interface through your browser (typically http://localhost:8501)

3. Enter the target directory for storing reports (default is "Documents/StockReports")

4. Enter a stock symbol and click "Analyze"

5. Monitor the analysis progress in real-time

6. Check the target directory for generated reports

## Directory Structure

The application creates the following directory structure:
```
Target Directory/
├── STOCK1/
│   ├── STOCK1_report_[timestamp].pdf
│   └── NSE_STOCK1_weekly_3years_[timestamp].csv
├── STOCK2/
│   ├── STOCK2_report_[timestamp].pdf
│   └── NSE_STOCK2_weekly_3years_[timestamp].csv
└── ...
```

## File Types Generated

- PDF Reports: Detailed analysis reports
- CSV Files: Historical stock data

## Error Handling

The application includes comprehensive error handling for:
- Invalid stock symbols
- Missing target directories
- Script execution failures
- File copying errors

## Dependencies

Main dependencies include:
- streamlit
- pandas
- numpy
- python-dateutil
- pytz
- pathlib
- platformdirs
- six
- packaging
- altair

For a complete list of dependencies, see `requirements.txt`.

## Troubleshooting

Common issues and solutions:

1. **Target Directory Access Error**
   - Ensure you have write permissions for the target directory
   - Try using a different directory path

2. **Script Execution Failures**
   - Check if analysis scripts are present in the correct directory
   - Verify script permissions
   - Check script dependencies

3. **File Not Found Errors**
   - Ensure the analysis scripts are generating files correctly
   - Check if specified paths exist and are accessible

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Create a new Pull Request

## License

[Your chosen license]

## Author

Manish Shrivastava

## Acknowledgments

- Thanks to all contributors
- List any third-party tools or libraries you want to acknowledge

## Support

For support and questions, please [open an issue](your-repository-issues-url) on the repository.
