class Config:
    def __init__(self):
        self.target_size = (224, 224)

        # HISTOGRAM
        self.hist_bins = (18,8,8)
        self.hist_ranges = [0,180,0,256,0,256]

        # HOG
        self.cell_size = 8
        self.block_size = 2
        self.hog_bins = 9

        # priority độ ưu tiên cái nào cao hơn thì được ưu tiên
        self.hog_w = 1.0
        self.his_w = 1.0
        