"""This script is used to download satelites images from Google Earth Engine."""
import os
import zipfile
import ee
import requests
from PIL import Image

# Initializes the import to get functionality
ee.Initialize()
# ee.Authenticate()


def combine_bands(image_object):
    """ This method combines the bands of images together

    Creates combined_bands as a expression of bands(images) added together
    """
    # Calculate the mean of the three bands
    combined_band = image.expression(
        '(b1 + b2 + b3) / 3', {
            'b1': image_object.select('B1'),
            'b2': image_object.select('B2'),
            'b3': image_object.select('B3')
        }).rename('combinedBand')

    # Normalize the combined band, by applying a reducer to find the max min of the entire region
    # Returns the a max and min
    min_max = combined_band.reduceRegion(ee.Reducer.minMax())

    #Pulls the max and min property
    min_val = ee.Number(min_max.get('combinedBand_min'))
    max_val = ee.Number(min_max.get('combinedBand_max'))

    #Applies the filter by setting the scale to the min and max,
    # then turns it into 8-byte to display
    normalized_combined_band = combined_band.unitScale(min_val, max_val).multiply(255).toByte()

    # Returns the combined bands as a property
    return image_object.addBands(normalized_combined_band)



#RnkUmmi -52.89 71.55 -51.43 71.82
#Creates a geometry object with cordinates of RnkUmmi
geometry = ee.Geometry.Rectangle([-52.89, 71.55, -51.43, 71.82])

DATA_PRODUCT = 'LANDSAT/LE07/C01/T1'
SEL_BANDS = ['B1','B2','B3']


#current dir
CURRENT_DIR = os.path.dirname(__file__)

#creates a temp folder to download the images to
SAVE_FOLDER = os.path.join(CURRENT_DIR,'RnkUmmi_Landsat-7')

#For loops that traverses all the years sequentially
for year in range(1999,2013):
    start = ee.Date(f'{year}-07-20')
    end = ee.Date(f'{year}-09-10')

    #This is a imageCollection object that has all the filters applied
    #Creates a new collection everytime there is a new year
    filteredCollection = (
        ee.ImageCollection(DATA_PRODUCT)
        .filterBounds(geometry)
        .filterDate(start, end)
        .select(SEL_BANDS)
        .filterMetadata('CLOUD_COVER', 'less_than', 30)
    )

    #Why is this list created? Its an object that holds pictures. Just need the pictures
    filtered_list=filteredCollection.toList(filteredCollection.size())

    #gets the count of the list
    filteredCount = filtered_list.size().getInfo()
    print(f"Filtered count is {filteredCount}")
    print(
    f"year is {year}, "
    f"{start.format('yyyy-MM-dd').getInfo()}" 
    f" and {end.format('yyyy-MM-dd').getInfo()}"
    )
    # for loop that traveses all the pictures in the list
    for i in range(filteredCount):
        #Make sure the list are inside the geometry object
        image = ee.Image(filtered_list.get(i)).clip(geometry)
        #Prints and formats the name of the GeoTIFF that is being downloaded
        fname = image.get('system:id').getInfo().split('/')[-1]

        image = combine_bands(image)
        print(f"Downloading {fname}")
        try:
            #creates the download url for the image
            url = image.getDownloadURL()
            #makes a request to download the image
            r=requests.get(url)
        except ConnectionError as e:
            print(f"Connection error: {e}")
        except TimeoutError as e:
            print(f"Time out error: {e}")
        except Exception as e:
            print(f"Failed to get Download URL: {e}")

        #names each file
        filename = f"data_{i}.zip"
        filepath = os.path.join(SAVE_FOLDER, filename)
        print(f"Downloading to: {filepath}, {i} in Filtered Count")
        try:
            #Download and saves the image
            with open(filepath, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print("Error failure to download")
        try:
            with zipfile.ZipFile(filepath) as f:
                files = f.namelist()
                f.extractall(SAVE_FOLDER)
                os.remove(filepath)
            print(f"Downloaded {filename}")
            print(f'Extracted {files} tif files from {filename}')
        except zipfile.BadZipFile:
            print('Skipping - Not a valid ZIP file')
        except Exception as e:
            print('Error extracting')


os.close()
print("Downloading complete")
