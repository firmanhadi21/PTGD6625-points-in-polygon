import streamlit as st
import folium
import geopandas as gpd
from shapely.geometry import Point
from streamlit_folium import folium_static

# Set up the Streamlit app
st.set_page_config(page_title="GeoJSON App")
st.title("GeoJSON App")



# Create the left sidebar and file uploader
st.sidebar.title("Upload Layers")
line_file = st.sidebar.file_uploader("Upload line layer", type=["geojson"])
building_file = st.sidebar.file_uploader("Upload building layer", type=["geojson"])
user_number = st.sidebar.number_input("Input Number",
                            min_value=1,
                            max_value=100,
                            value=25,
                            step=1)
st.write(user_number)

# Create a default map
default_location = [-6.96, 110.48]
default_zoom = 12
map = folium.Map(location=default_location, zoom_start=default_zoom)
folium.TileLayer('openstreetmap').add_to(map)
folium_static(map)

# Define a buffer distance
buffer_dist = user_number

if line_file and building_file:
    # Create a buffer from the line
    line_layer = gpd.read_file(line_file)
    buffer_layer = line_layer.buffer(buffer_dist)
    buffer_layer.to_file("buffer.geojson", driver="GeoJSON")
    
    # Convert buildings to points
    building_layer = gpd.read_file(building_file)
    point_layer = building_layer.centroid
    point_layer.to_file("points.geojson", driver="GeoJSON")
    
    # Count the points within the buffer
    buffer_layer = gpd.read_file("buffer.geojson")
    point_layer = gpd.read_file("points.geojson")
    points_within_buffer = point_layer[point_layer.within(buffer_layer.unary_union)]
    count = len(points_within_buffer)
    
    # Show the result
    st.sidebar.write(f"Count of buildings within {buffer_dist} meters of the line: {count}")
    
    # Make the result dynamic
    folium.GeoJson(line_layer, name="Line layer", style_function=lambda feature: {'color': 'blue'}).add_to(map)
    folium.GeoJson(buffer_layer, name="Buffer layer", style_function=lambda feature: {'color': 'red', 'fillOpacity': 0.2}).add_to(map)
    folium.LayerControl().add_to(map)
    
    # Define a function to update the count and circle marker on the map
    def update_map(event):
        points_within_buffer = point_layer[point_layer.within(buffer_layer.unary_union)]
        count = len(points_within_buffer)
        st.sidebar.write(f"Count of buildings within {buffer_dist} meters of the line: {count}")
        map = folium.Map(location=[event['location'][0], event['location'][1]], zoom_start=event['zoom'])
        folium.TileLayer('openstreetmap').add_to(map)
        folium.GeoJson(line_layer, name="Line layer", style_function=lambda feature: {'color': 'blue'}).add_to(map)
        folium.GeoJson(buffer_layer, name="Buffer layer", style_function=lambda feature: {'color': 'red', 'fillOpacity': 0.2}).add_to(map)
        folium.CircleMarker(location=[event['location'][0], event['location'][1]], radius=count/10, 
                            color='red', fill=True, fill_opacity=0.7).add_to(new_map)
        folium.LayerControl().add_to(map)
        folium_static(map)
    
    # Update the map when the user pans or zooms
    map.add_child(folium.MacroElement().add_to(map).add_child(folium.Element(
        """
        <script>
        var me = this;
        me.on('moveend', function() {
            var center = me.getCenter();
            var zoom = me.getZoom();
            var event = {'location': [center.lat, center.lng], 'zoom': zoom};
            parent.postMessage(event, '*');
        });
        </script>
        """
    )))
    
    # Use Streamlit to receive the events and update the map
    if 'new_location' not in st.session_state:
        st.session_state.new_location = None
    new_location = st.session_state.new_location
    if new_location:
        update_map(new_location)
