import ee
ee.Initialize()
import requests
import os
import zipfile

vis_params_bw = {
    'min': 0,
    'max': 255,
    'palette': ['black', 'white']
}

def combine_bands(image):
    # Calculate the mean of the three bands
    combined_band = image.expression(
        '(b1 + b2 + b3) / 3', {
            'b1': image.select('B1'),
            'b2': image.select('B2'),
            'b3': image.select('B3')
        }).rename('combinedBand')

    # Normalize the combined band
    min_max = combined_band.reduceRegion(ee.Reducer.minMax())

    min_val = ee.Number(min_max.get('combinedBand_min'))
    max_val = ee.Number(min_max.get('combinedBand_max'))

    normalized_combined_band = combined_band.unitScale(min_val, max_val).multiply(255).toByte()

    return image.addBands(normalized_combined_band)



#RnkUmmi -52.89 71.55 -51.43 71.82
#Creates a geometry object with cordinates of RnkUmmi
geometry = ee.Geometry.Rectangle([-52.89, 71.55, -51.43, 71.82])

data_product = 'LANDSAT/LE07/C01/T1'
sel_bands = ['B1','B2','B3']

#creates a temp folder to download the images to
save_folder = 'RnkUmmi_Landsat-7-test'
os.makedirs(save_folder, exist_ok=True)

#For loops that traverses all the years sequentially
for year in range(1999,2013):
    start = ee.Date(f'{year}-07-20')
    end = ee.Date(f'{year}-09-10')

    #This is a imageCollection object that has all the filters applied
    #Creates a new collection everytime there is a new year 
    filteredCollection = (
        ee.ImageCollection(data_product)
        .filterBounds(geometry)
        .filterDate(start, end)
        .select(sel_bands)
        .filterMetadata('CLOUD_COVER', 'less_than', 30)
    ) 
    

    #Why is this list created? Its an object that holds pictures. Just need the pictures
    filtered_list=filteredCollection.toList(filteredCollection.size())

    #gets the count of the list 
    filteredCount = filtered_list.size().getInfo()
    print("Filtered count is %d"%(filteredCount))
    print(f"year is {year}, {start.format('YYYY-MM-dd').getInfo()} and {end.format('YYYY-MM-dd').getInfo()}")
    # for loop that traveses all the pictures in the list
    for i in range(filteredCount):
        #Make sure the list are inside the geometry object
        image = ee.Image(filtered_list.get(i)).clip(geometry)
        #Prints and formats the name of the GeoTIFF that is being downloaded
        fname = image.get('system:id').getInfo().split('/')[-1]

        image = combine_bands(image) 
        print("downloading %s"%fname)

        try:
            #creates the download url for the image
            url = image.getDownloadURL()

            #makes a request to download the image
            r=requests.get(url)

            print(url)
        except Exception as e:
            print("Failed to get Download URL")

        # #names each file 
        # filename = f"data_{i}.zip"
        # filepath = os.path.join(save_folder, filename)
        # print(f"Downloading to: {filepath}, {i} in Filtered Count")
        # try:
        #     #Download and saves the image
        #     with open(filepath, 'wb') as f:
        #         f.write(r.content)
        # except Exception as e:
        #     print(f"Error failure to download")
        # try:
        #     with zipfile.ZipFile(filepath) as f:
        #         files = f.namelist()
        #         f.extractall(save_folder)
        #     os.remove(filepath)
        #     print(f"Downloaded {filename}")
        #     print(f'Extracted {files} tif files from {filename}')
        # except zipfile.BadZipFile:
        #     print('Skipping - Not a valid ZIP file')
        # except Exception as e:
        #     print('Error extracting')

print("Downloading complete")
