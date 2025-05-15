# Cellfinder

This is a small code to find cells that are positively transfected

To launch the script, you must have a session of Metamorph or Micromanager open. 
Two parameters should be changed : the step (distance between two images) and the range in the loops (number of steps in each direction)

The principle is simple: the script cellfinder.py scans the coverslip you are looking at, takes pictures and saves positions (and picture) when it finds a cell. 
The tool select_good_positions.py is a streamlit app to select the cells you want to keep, and it will create a position file, which can be imported in Metamorph or in Micromanager. It should be run using 'streamlit run select_good_positions.py'
