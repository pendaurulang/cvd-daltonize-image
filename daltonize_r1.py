import os

def execute(filename, fpath, color_deficit='d'):
    modified_filename = ("%s-%s-%s" % ('daltonize', color_deficit, filename))
    head, tail = os.path.split(fpath)
    fname, ext = os.path.splitext(tail)
    # Save transformed image to the cache dir 
    #head = head.replace('attachments', 'cache')
    dalton = os.path.join(fname,'daltonized')
    results = os.path.join('results',dalton)
    modified_path = os.path.join(head, results)
    modified_fpath = os.path.join(modified_path, modified_filename)

    # Look if requested image is already available
    if os.path.isfile(modified_fpath):
        return (modified_filename, modified_fpath)
    if  not os.path.isdir(os.path.join(head,'results')) :
        os.mkdir(os.path.join(head,'results'))
    if  not os.path.isdir(os.path.join(head,'results',fname)) :
        os.mkdir(os.path.join(head,'results',fname))
    if  not os.path.isdir(modified_path) :
        os.mkdir(modified_path) 

    helpers_available = True
    try:
        import numpy
        from PIL import Image
    except:
        helpers_available = False
    if not helpers_available:
        return (filename, fpath)

    # Get image data
    im = Image.open(fpath)
    if im.mode in ['1', 'L']: # Don't process black/white or grayscale images
        return (filename, fpath)
    im = im.copy() 
    im = im.convert('RGB') 
    RGB = numpy.asarray(im, dtype=float)

    # Transformation matrix for Deuteranope (a form of red/green color deficit)
    lms2lmsd = numpy.array([[1,0,0],[0.494207,0,1.24827],[0,0,1]])
    # Transformation matrix for Protanope (another form of red/green color deficit)
    lms2lmsp = numpy.array([[0,2.02344,-2.52581],[0,1,0],[0,0,1]])
    # Transformation matrix for Tritanope (a blue/yellow deficit - very rare)
    lms2lmst = numpy.array([[1,0,0],[0,1,0],[-0.395913,0.801109,0]])
    # Colorspace transformation matrices
    rgb2lms = numpy.array([[17.8824,43.5161,4.11935],[3.45565,27.1554,3.86714],[0.0299566,0.184309,1.46709]])
    lms2rgb = numpy.linalg.inv(rgb2lms)
    # Daltonize image correction matrix
    err2mod = numpy.array([[0,0,0],[0.7,1,0],[0.7,0,1]])

    # Get the requested image correction
    if color_deficit == 'd':
        lms2lms_deficit = lms2lmsd
    elif color_deficit == 'p':
        lms2lms_deficit = lms2lmsp
    elif color_deficit == 't':
        lms2lms_deficit = lms2lmst
    else:
        return (filename, fpath)
    
    # Transform to LMS space
    LMS = numpy.zeros_like(RGB)               
    for i in range(RGB.shape[0]):
        for j in range(RGB.shape[1]):
            rgb = RGB[i,j,:3]
            LMS[i,j,:3] = numpy.dot(rgb2lms, rgb)

    # Calculate image as seen by the color blind
    _LMS = numpy.zeros_like(RGB)  
    for i in range(RGB.shape[0]):
        for j in range(RGB.shape[1]):
            lms = LMS[i,j,:3]
            _LMS[i,j,:3] = numpy.dot(lms2lms_deficit, lms)

    _RGB = numpy.zeros_like(RGB) 
    for i in range(RGB.shape[0]):
        for j in range(RGB.shape[1]):
            _lms = _LMS[i,j,:3]
            _RGB[i,j,:3] = numpy.dot(lms2rgb, _lms)

   # Save simulation how image is perceived by a color blind
    for i in range(RGB.shape[0]):
       for j in range(RGB.shape[1]):
           _RGB[i,j,0] = max(0, _RGB[i,j,0])
           _RGB[i,j,0] = min(255, _RGB[i,j,0])
           _RGB[i,j,1] = max(0, _RGB[i,j,1])
           _RGB[i,j,1] = min(255, _RGB[i,j,1])
           _RGB[i,j,2] = max(0, _RGB[i,j,2])
           _RGB[i,j,2] = min(255, _RGB[i,j,2])
    simulation = _RGB.astype('uint8')
    im_simulation = Image.fromarray(simulation, mode='RGB')
    simulation_filename = "%s-%s-%s" % ('daltonize-simulation', color_deficit, filename)
    sims = os.path.join('results',fname,"sims")
    sims_path = os.path.join(head, sims)
    if  not os.path.isdir(sims_path) :
        os.mkdir(sims_path)
    simulation_fpath = os.path.join(sims_path, simulation_filename)
    im_simulation.save(simulation_fpath)

    # Calculate error between images
    error = (RGB-_RGB)

    # Daltonize
    ERR = numpy.zeros_like(RGB) 
    for i in range(RGB.shape[0]):
        for j in range(RGB.shape[1]):
            err = error[i,j,:3]
            ERR[i,j,:3] = numpy.dot(err2mod, err)

    dtpn = ERR + RGB
    
    for i in range(RGB.shape[0]):
        for j in range(RGB.shape[1]):
            dtpn[i,j,0] = max(0, dtpn[i,j,0])
            dtpn[i,j,0] = min(255, dtpn[i,j,0])
            dtpn[i,j,1] = max(0, dtpn[i,j,1])
            dtpn[i,j,1] = min(255, dtpn[i,j,1])
            dtpn[i,j,2] = max(0, dtpn[i,j,2])
            dtpn[i,j,2] = min(255, dtpn[i,j,2])

    result = dtpn.astype('uint8')
    
    # Save daltonized image
    im_converted = Image.fromarray(result, mode='RGB')
    im_converted.save(modified_fpath)
    return (modified_filename, modified_fpath)

def getpath(directory):
    dirlist =os.listdir(directory)
    s_dirlist=[]
    for f in dirlist:
        fname, ext = os.path.splitext(f)
        if ext == ".jpg":
            s_dirlist.append(f)
    return s_dirlist



if __name__ == '__main__':
    import sys
    print ("Daltonize image correction for color blind users")
    
    if len(sys.argv) != 2:
        print ("Calling syntax: daltonize.py [fullpath to image file]")
        print ("Example: daltonize_r1.py /usr/data/pages/PageName/attachments/")
        sys.exit(1)

    if not (os.path.isdir(sys.argv[1])):
        print ("Given dir does not exist")
        sys.exit(1)

    # extpos = sys.argv[1].rfind(".")
    # if not (extpos > 0 and sys.argv[1][extpos:].lower() in ['.gif', '.jpg', '.jpeg', '.png', '.bmp', '.ico', ]):
    #     print ("Given file is not an image")
    #     sys.exit(1)

    # path, fname = os.path.split(sys.argv[1])
    print ("Please wait. Daltonizing in progress...")
    img_path=getpath(sys.argv[1])

    colorblindness = { 'd': 'Deuteranope',
                       'p': 'Protanope',
                       't': 'Tritanope',}
    image_count=0
    for fname in img_path:                            
        for col_deficit in ['d', 'p', 't']:
            print ("Creating %s corrected version" % colorblindness[col_deficit])
            image_path = os.path.join(sys.argv[1],fname)
            modified_filename, modified_fpath = execute(fname, image_path, col_deficit)
            if modified_fpath == image_path:
                print ("Error while processing image: PIL/NumPy missing and/or source file is a grayscale image.")
            else:
                print ("Image %s successfully daltonized" % fname)
        image_count=image_count+1
        print("%s image converted" %image_count)
    print("total image converted :",image_count)