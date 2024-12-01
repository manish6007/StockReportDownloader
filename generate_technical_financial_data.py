import subprocess
import sys
import time

def validate_symbol(symbol):
    """
    Validate the input symbol
    
    Parameters:
    symbol (str): Company symbol
    
    Returns:
    str: Validated symbol
    """
    if not symbol:
        raise ValueError("Company symbol cannot be empty")
        
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError("Company symbol should only contain letters and numbers")
        
    return symbol

def execute_script(script_name, symbol):
    """
    Execute a Python script with the given symbol argument
    
    Parameters:
    script_name (str): Name of the script to execute
    symbol (str): Company symbol to pass as argument
    
    Returns:
    bool: True if execution was successful, False otherwise
    """
    try:
        print(f"\nExecuting {script_name} for {symbol}...")
        result = subprocess.run(
            [sys.executable, script_name, symbol],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Output from {script_name}:")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_name}:")
        print(f"Exit code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False
        
    except Exception as e:
        print(f"Unexpected error executing {script_name}: {str(e)}")
        return False

def main():
    print("Company Analysis Tool")
    print("=" * 50)
    
    while True:
        try:
            # Get symbol from user
            symbol = input("\nPlease enter company symbol you want to analyse (or 'q' to quit): ")
            
            # Check for quit command
            if symbol.lower() == 'q':
                print("\nExiting program.")
                break
                
            # Validate symbol
            symbol = validate_symbol(symbol)
            
            # Define scripts to execute
            scripts = [
                'crawl_screener_generate_report_in_folder.py',
                'download_candledata_in_folder.py'
            ]
            
            # Execute each script
            success_count = 0
            for script in scripts:
                if execute_script(script, symbol):
                    success_count += 1
                time.sleep(1)  # Add small delay between scripts
            
            # Report overall status
            if success_count == len(scripts):
                print(f"\nSuccessfully completed all analyses for {symbol}")
            else:
                print(f"\nCompleted with some errors. {success_count} out of {len(scripts)} scripts succeeded for {symbol}")
                
        except ValueError as e:
            print(f"\nError: {str(e)}")
            continue
            
        except KeyboardInterrupt:
            print("\n\nProgram terminated by user.")
            break
            
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            continue

if __name__ == "__main__":
    main()