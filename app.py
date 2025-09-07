import streamlit as st
from streamlit_option_menu import option_menu
from openai import OpenAI
import base64
from datetime import datetime
import sqlite3
import pandas as pd

# Initialize OpenAI client
apiKey = ''
client = OpenAI(api_key=apiKey)

# Initialize session state if not exists
if 'chatHistory' not in st.session_state:
    st.session_state.chatHistory = {"ques": [], "ans": [], "timestamp": []}

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def output(query, cho, paths):
    if cho == "Attach image":
        base64_images = [encode_image(path.name) for path in paths]
        image_urls = [f"data:image/png;base64,{base64_img}" for base64_img in base64_images]
        
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": query}
            ] + [
                {"type": "image_url", "image_url": {"url": url}}
                for url in image_urls
            ]}
        ]
        
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages,
            temperature=0.0,
        )
        
        return response.choices[0].message.content

# Function to get table names from the database
def get_table_names():
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    conn.close()
    return [table[0] for table in tables]

# Function to fetch data from the selected table
def fetch_table_data(table_name):
    conn = sqlite3.connect('history.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    data = c.fetchall()
    conn.close()
    return data

# Function to generate a title
def generate_title(prompt):
    completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a helpful assistant. You are going to choose an appropriate title for the given string like chatgpt chooses the chat title"}, 
        {"role": "user", "content": f"give me a suitable title for this {prompt}"}  
      ]
    )
    
    return completion.choices[0].message.content


def generate_matplotlib_code(description):
    prompt = """
    Generate a Python function named generate_plan that creates a Matplotlib figure representing the following floorplan description with the specified labels, dimensions, and positions. 
    The function should:
    - Create the floorplan using Matplotlib
    - Ensure correct positions and dimensions of each element
    - the drawing should be scaled. include the scale in the image.
    - Annotate the elements with the specified labels and dimensions
    - Return only the figure (fig)
    -in annotations, mention feet and inches instead of ' and ". eg., 15'-5" as 15feet-5inch
    -the label should be in ax.text and the dimensions should be in another ax.text. not in same
    -make the font size small

    Provide only the function definition as the response, nothing else.
    An example output with desired format:
import matplotlib.pyplot as plt

def generate_plot():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2, 3], [10, 20, 25, 30])
    ax.set_title("Sample Plot")
    return fig

    """

    # Combine prompt and user description
    combined_prompt = f"{prompt} {description}"
    
    messages = [
        {"role": "system", "content": "You are an expert in generating Python Matplotlib code for visualizing floorplans. You understand how to create simple, rough floorplan diagrams using Python Matplotlib. You ensure that the orientations and positions of different elements are accurate. There are no overlaps between the elements."},
        {"role": "user", "content": combined_prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
    )

    function_code = response.choices[0].message.content
    return function_code

def execute_function_code(function_code, function_name, *args, **kwargs):
    # Execute the function code string
    exec(function_code, globals())
    # Call the function with the provided arguments
    return globals()[function_name](*args, **kwargs)


# Streamlit UI
st.set_page_config(page_title="VisualChat with GPT-4o")

# Sidebar with options and image handling
st.sidebar.image("https://image.pitchbook.com/Tf5tfYnTZayaB4Yx7cSABAXNnaR1638562088465_200x200", width=200)

with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["Home", "History", "New Chat", "Prev Chats","Generate", "Guide"],
        icons=["house","clock-history", "plus-circle","rewind","card-image","book"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

cho = st.sidebar.selectbox("Select", ["None", "Attach image", "Paste the image link"])

col1, col2 = st.columns(2)    

img = None
if cho == "Attach image":
    img = st.sidebar.file_uploader("Upload the image(s)", accept_multiple_files=True)
    with col2:
        if img:
            st.image(img,use_column_width=True)
            
elif cho == "Paste the image link":
    img = st.sidebar.text_area("Enter the image link")
    with col2:
        if img:
            st.image(img,use_column_width=True)

if selected == "Guide":          
    st.markdown("<h1 style='text-align: center;'>App Guide</h1>", unsafe_allow_html=True)
    
    with st.expander("Overview and Components"):
        st.markdown(
        """
        ## Overview
        This Streamlit app allows users to interact with an AI chatbot powered by OpenAI's GPT-4o model. Users can enter queries, attach images, and save chat histories to a SQLite database.

        ## Components

        1. **Sidebar Navigation**
           - Provides navigation options: Home, History, New Chat, Prev Chats.
           - Options are represented with icons for clarity.

        2. **Image Handling**
           - Users can attach images via file upload or by pasting image links.
           - Selected images are displayed in real-time.

        3. **Chat Interface**
           - **Home**: Enter queries and interact with the chatbot.
           - Messages are displayed with timestamps.

        4. **Saving Chats**
           - **New Chat**: Save the current chat session to a SQLite database.
           - Option to generate a title automatically or enter a custom title.
           - Chat history is cleared after saving.

        5. **History**
           - Displays current session chat history with questions, responses, and timestamps.

        6. **Previous Chats**
           - Select and fetch historical chats stored in the SQLite database.
           - Option to delete selected chat history.
           
        7. **Dynamic Plot Generation**
           - **Generate**: Create floorplan visualizations based on user-provided descriptions.
           - Use Matplotlib to dynamically generate and display floorplan images.
           """)
    
    with st.expander("Usage Guide"):
        st.markdown("""
        ### Home (Chat Interface)
        - Enter your query in the text input field.
        - Select image attachment options (Upload image, Paste image link).
        - Interact with the chatbot and view responses in real-time.

        ### New Chat (Save Chat)
        - Click "New Chat" to save the current chat session.
        - Choose to generate a title automatically or enter a custom title.
        - Once saved, the chat history is cleared for a new session.

        ### History
        - View current session chat history, including questions, responses, and timestamps.
        - Helpful for reviewing recent interactions.

        ### Previous Chats
        - Select from dropdown to fetch and view historical chat sessions stored in the database.
        - Buttons to fetch or delete selected chat history.
        
        #### Dynamic Plot Generation

        - **Generate Image**: Provide a floorplan description and click to generate visualizations.
        - Matplotlib is used to create and display floorplan images based on user-provided descriptions.

        ## Additional Features
        - **CSS Customization**: Positions input at the bottom and adds styling for a cleaner UI.
        - **Image Handling**: Supports image upload and link pasting within the chat interface.
        - **Error Handling**: Displays errors or success messages during operations like saving or deleting chats.
        """
    )            

# Main content
with col1:
    if selected == "Home":
        output_container = st.container()       
        query = st.text_input("Enter your query", placeholder="Type here")
        if query and cho and img:
            with output_container:
                st.write("You : " + query)
                st.session_state.chatHistory["ques"].append(query)
                resp = output(query, cho, img)
                st.info(resp)
                st.session_state.chatHistory["ans"].append(resp)
                st.session_state.chatHistory["timestamp"].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Custom CSS for positioning the input at the bottom and adding a red rectangle block
st.markdown(
    """
    <style>
    .stTextInput {
        position: fixed;
        bottom: 0;
        width: 50%;
        left: 25%; 
        background-color: #f0f0f0;
        border: 1px solid #cccccc;
        padding: 10px;
        z-index: 10;
    }
    .stTextInput input {
        background-color: #d4d4d4;
        width: 100%;
        border: none;
        outline: none;
        padding: 5px;
        font-size: 14px;
        border-radius: 5px;
        box-sizing: border-box;
    }
    
    .white-space1 {
        position: fixed;
        bottom: 0;
        left:0;
        width: 25%;
        height: 15.1%;
        background-color: white;
    }
    
    .white-space2 {
        position: fixed;
        right:6px;
        bottom: 0;
        width: 24.487%;
        height: 15.1%;
        background-color: white;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

if selected == "Home":
    st.markdown('<div class="white-space1"></div>', unsafe_allow_html=True)
    st.markdown('<div class="white-space2"></div>', unsafe_allow_html=True)

# variable for title
head = ""
# Handle "New Chat" button click
if selected == "New Chat":
    if st.session_state.chatHistory["ques"] and st.session_state.chatHistory["ans"]:
        st.markdown("<h1 style='text-align: center;'>Save Chat</h1>", unsafe_allow_html=True)
        
        opt = ["Enter custom title", "Generate a title"]
        rb = st.radio("Title for the chat",options=opt,index=0)
        
        if rb == "Enter custom title":
            head = st.text_area("Enter the title")
        else:
            btn = st.button("Generate Title")
            if btn:
                head = generate_title(st.session_state.chatHistory["ques"])
                st.write("Generated Title : " + head)
        
        if head !="" and not head.isspace() and head != None:
            st.success("The chat has been saved")
        
            # Connect to the database (or create it if it doesn't exist)
            conn = sqlite3.connect('history.db')
        
            # Create a cursor object
            cursor = conn.cursor()
        
            # Create table with specified columns
            table_name = '_'.join(head.split())
            
            create_query = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            '''
            cursor.execute(create_query)
            conn.commit()    
            
            for i in range(len(st.session_state.chatHistory["ques"])):
                val1 = st.session_state.chatHistory["ques"][i]
                val2 = st.session_state.chatHistory["ans"][i]
                val3 = st.session_state.chatHistory["timestamp"][i]
                
                # Insert data into the table
                insert_query = f'''INSERT INTO {table_name} VALUES (?, ?, ?)'''
                cursor.execute(insert_query, (val1, val2, val3))
                conn.commit() 
            
            # Close the connection
            conn.close()
            
            # Clear session state
            st.session_state.chatHistory = {"ques": [], "ans": [], "timestamp": []}
        
            # Reset UI elements
            query = None
            cho = None
            img = None

    else:
        st.warning("The chat is currently empty. Please enter a query to begin.")
        
# Display chat history if "History" is selected
if selected == "History":
    st.markdown("<h1 style='text-align: center;'>Chat History</h1>", unsafe_allow_html=True)
    # Ensure all lists have the same length before displaying the table
    min_length = min(len(st.session_state.chatHistory["ques"]), 
                     len(st.session_state.chatHistory["ans"]), 
                     len(st.session_state.chatHistory["timestamp"]))
    
    history_data = {
        'Question': st.session_state.chatHistory["ques"][:min_length],
        'Response': st.session_state.chatHistory["ans"][:min_length],
        'Timestamp': st.session_state.chatHistory["timestamp"][:min_length]
    }
    
    st.table(history_data)

# Display database tables if "Prev Chats" is selected
if selected == "Prev Chats":
    st.markdown("<h1 style='text-align: center;'>Previous Chat History</h1>", unsafe_allow_html=True)
    
    # Get table names
    table_names = get_table_names()
    # Replacing the underscore with space for table name
    tables_names = [" ".join(i.split("_")).capitalize() for i in table_names]
    # Dropdown to select chat, display the chats in the reverse order
    selected_table = st.selectbox("Select a chat", tables_names[::-1])
    
    btn1, _, _, _, _, btn2 = st.columns(6)
    
    # Variables to track if buttons were clicked
    fetch_clicked = False
    delete_clicked = False

    # Button to fetch data from the selected table
    with btn1:
        if st.button("Fetch Chat"):
            fetch_clicked = True

    with btn2:
        if st.button("Delete Chat"):
            delete_clicked = True

    if fetch_clicked and selected_table:
        table_data = fetch_table_data("_".join(selected_table.lower().split()))
        df = pd.DataFrame(table_data)
        df.columns = ["Question", "Response", "Timestamp"]
        st.table(df)
    
    if delete_clicked and selected_table:
        conn = sqlite3.connect('history.db')
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {'_'.join(selected_table.lower().split())}")
        conn.commit()
        conn.close()
        st.success("Table deleted successfully.")
        
fig=None    
if selected == "Generate":
    st.markdown("<h1 style='text-align: center;'>Dynamic Plot Generator</h1>", unsafe_allow_html=True)
    
    inp,gen = st.columns(2)
    with gen:
        with st.expander("Syntax"):
            st.markdown("""
                    **Floorplan Description:**
                    - **Overall Dimensions:** `Overall Dimensions`
                    - **Orientation:** `Orientation`
                    
                    **Rooms and Dimensions:**
                    
                    1. **Living Room:**
                       - **Location:** `Living Room Location`
                       - **Dimensions:** `Living Room Dimensions`
                       - **Entry:** `Living Room Entry`
                    
                    2. **Hallway:**
                       - **Location:** `Hallway Location`
                       - **Dimensions:** `Hallway Dimensions`
                       - **Entry:** `Hallway Entry`
                    
                    3. **Kitchen:**
                       - **Location:** `Kitchen Location`
                       - **Dimensions:** `Kitchen Dimensions`
                       - **Entry:** `Kitchen Entry`
                    
                    4. **Master Bedroom (M.B.E.D):**
                       - **Location:** `Master Bedroom Location`
                       - **Dimensions:** `Master Bedroom Dimensions`
                       - **Entry:** `Master Bedroom Entry`
                       - **Attached Bath:**
                         - **Location:** `Attached Bath Location`
                         - **Dimensions:** `Attached Bath Dimensions`
                    
                    5. **Bedroom 1 (B.E.D):**
                       - **Location:** `Bedroom 1 Location`
                       - **Dimensions:** `Bedroom 1 Dimensions`
                       - **Entry:** `Bedroom 1 Entry`
                    
                    6. **Common Bath:**
                       - **Location:** `Common Bath Location`
                       - **Dimensions:** `Common Bath Dimensions`
                       - **Entry:** `Common Bath Entry`
                    
                    **Spacing and Orientation:**
                    - `Room A` is located `Location A`, accessible from `Room B`.
                    - `Room B` is centrally located, providing access to all other rooms.
                    - `Room C` is located `Location C`, adjacent to `Room D`.
                    """)
        
        with st.expander("Example 1"):
            st.markdown("""

                            
                        	**Floorplan Description** *(Copy & Edit)*\n
                            o Overall Dimensions: 40' x 36'
                            o Orientation: North is at the top of the plan.
                            
                            Rooms and Dimensions:
                            1.	Drawing Room:
                            o	Location: Bottom-left corner.
                            o	Dimensions: 15'-5" x 14'-4"
                            o	Entry: From the central dining area.
                            
                            2.	Dining Area:
                            o	Location: Center of the plan.
                            o	Dimensions: 9'-0" x 20'-3"
                            o	Entry: Accessible from the drawing room, kitchen, and bedrooms.
                            
                            3.	Kitchen:
                            o	Location: Top-right corner.
                            o	Dimensions: 11'-0" x 9'-0"
                            o	Entry: From the dining area.
                            
                            4.	Master Bedroom (M.B.E.D):
                            o	Location: Top-right, adjacent to the kitchen.
                            o	Dimensions: 12'-0" x 11'-0"
                            o	Entry: From the dining area.
                            o	Attached Bath:
                            	Location: Top-right corner.
                            	Dimensions: 7'-1" x 4'-0"
                            
                            5.	Bedroom 1 (B.E.D):
                            o	Location: Top-left corner.
                            o	Dimensions: 11'-0" x 11'-0"
                            o	Entry: From the dining area.
                            
                            6.	Bedroom 2 (B.E.D):
                            o	Location: Top-center.
                            o	Dimensions: 11'-0" x 11'-0"
                            o	Entry: From the dining area.
                            
                            7.	Master Bedroom (M.B.E.D):
                            o	Location: Bottom-right corner.
                            o	Dimensions: 11'-0" x 14'-4"
                            o	Entry: From the dining area.
                            o	Attached Bath:
                            	Location: Bottom-right corner.
                            	Dimensions: 9'-0" x 4'-0"
                            
                            8.	Common Bath:
                            o	Location: Top-left, adjacent to Bedroom 1.
                            o	Dimensions: 7'-1" x 4'-7"
                            o	Entry: From the dining area.
                            
                            9.	Staircase:
                            o	Location: Bottom-center.
                            o	Dimensions: 7'-6" x 17'-10"
                            o	Entry: From the dining area.
                            
                            Spacing and Orientation:
                            •	The drawing room is directly accessible from the dining area and is located on the left side of the plan.
                            •	The dining area is centrally located, providing access to all other rooms.
                            •	The kitchen is located on the right side of the plan, adjacent to the master bedroom.
                            •	The bedrooms are located on the top side of the plan, with two bedrooms on the left and one master bedroom on the right.
                            •	The staircase is centrally located at the bottom of the plan, providing access to other floors.
                            •	The common bath is located adjacent to Bedroom 1 on the top-left side of the plan.
                            •	The master bedroom on the bottom-right has an attached bath, accessible from within the room. 
                            """)
        
        with st.expander("Example 2"):
            st.markdown("""

                            
                        	**Floorplan Description** *(Copy & Edit)*\n
                            o Overall Dimensions: 30' x 20'
                            o Orientation: North is at the top
                            
                            Rooms and Dimensions:
                            1.	Living Room:
                            o	Location: Bottom-left corner
                            o	Dimensions: 15' x 12'
                            o	Entry: From the main hallway
                            
                            2.	Kitchen:
                            o	Location: Bottom-right corner
                            o	Dimensions: 10' x 8'
                            o	Entry: From the dining area
                            
                            3.	Master Bedroom:
                            o	Location: Top-left corner
                            o	Dimensions: 12' x 10'
                            o	Entry: From the main hallway
                            o	Attached Bath:
                            	Location: Adjacent to the bedrrom
                            	Dimensions: 6' x 5'
                            
                            4.	Bedroom 1:
                            o	Location: Top-right corner
                            o	Dimensions: 10' x 10'
                            o	Entry: From the main hallway
                            
                            Spacing and Orientation:
                            •	The living room is located on the left side of the plan, accessible from the main hallway.
                            •   The kitchen is on the right side, adjacent to the dining area.
                            •   The bedrooms are located on the top side of the plan, with the master bedroom on the left and Bedroom 1 on the right. 
                            """)
    
    with inp:    
        description = st.text_area("Enter the description of the floorplan")
       
        if st.button("Generate Image"):
            if description:
                # Assuming the function name generated by GPT is 'generate_plot'
                function_name = 'generate_plan'
                function_code = generate_matplotlib_code(description)
                function_code = function_code.replace('python', '')
                function_code = function_code.replace('```', '')
                # Execute the function and get the figure
                fig = execute_function_code(function_code, function_name)               
            else: 
                st.warning("Please enter a description of the floorplan.")
    if fig:

        st.pyplot(fig)
