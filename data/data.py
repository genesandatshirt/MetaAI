from fastai.basic_data import *
from fastai.vision import *
import pandas as pd

class MetaDataBunch():
    "Each MetaDataBunch has a list of train and validation tasks. Each task is an ImageDataBunch with fixed number of train examples."
    #changes made to basic_data.py line 118-119
    def __init__(self,path:PathOrStr, df:pd.DataFrame, folder:PathOrStr=None, label_delim:str=None, valid_pct:float=0.2,
                seed:int=None, fn_col:IntsOrStrs=0, label_col:IntsOrStrs=1, suffix:str='', size=32, bs=100, shots=5, ways=20,**kwargs:Any)->'MetaDataBunch':        
        
        if seed:
            np.random.seed(seed)
        sampling = np.arange(df[label_col].nunique())
        np.random.shuffle(sampling)
        df[label_col] = pd.factorize(df[label_col],sort=True)[0]        
        def split_meta(self,shots,col):
            "Split the items giving the train_dl fixed number of examples of each class, while remaining go to valid_dl"
            df = self.inner_df.set_index(self.inner_df.columns[col]).reset_index()
            train_df = pd.concat([g.sample(shots,replace=False) for _,g in df.groupby(label_col)])
            train_idx = train_df.index.values
            valid_idx = np.setdiff1d(arange_of(self.items),train_idx)
            return self.split_by_idxs(train_idx,valid_idx)
        ImageList.split_meta = split_meta
        
        # Split all classes in meta dataset into tasks each with "ways" number of classes
        # sampling = self.chunk(sampling,ways)
        # Make a list of sub dataframes having the filenames of images in each task
        # df_list = [df[df[label_col].isin(l)] for l in sampling]   
        df_list = self.chunk(df,sampling,ways)   
        
        meta_train_dfs = df_list[:-int(valid_pct*len(df_list))]
        meta_valid_dfs = df_list[-int(valid_pct*len(df_list)):]
        
        self.train_tasks = [self.produce_databunch(d) for d in meta_train_dfs]
        self.valid_tasks = [self.produce_databunch(d) for d in meta_valid_dfs]

    def chunk(self,df,l,n):
        sampling = [l[i:i+n] for i in range(0, len(l), n)]
        df_list = [df[df[self.label_col].isin(l)] for l in sampling]  
        return df_list
    
    def produce_databunch(self,df):
        "Make a databunch from df"
        # db = ImageList.from_df(df,path=path,folder=folder,suffix=suffix, cols=fn_col)
        # db = (db.split_meta(shots,fn_col)
        #        .label_from_df(label_delim=label_delim, cols=label_col))
        # db = ImageDataBunch.create_from_ll(db,bs=bs,**kwargs).normalize(imagenet_stats)
        db = (ImageList.from_df(df,path=path,folder=folder,suffix=suffix, cols=fn_col).
                split_none().
                label_from_df(label_delim=label_delim, cols=label_col).
                transform(size=size).
                databunch(bs=bs,num_workers=os.cpu_count()).
                normalize(imagenet_stats))
        db.train_dl = db.train_dl.new(shuffle=False)
        return db

class MAMLMetaDataBunch(MetaDataBunch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

class ReptileMetaDataBunch(MetaDataBunch):
    def __init__(self,path:PathOrStr, df:pd.DataFrame, folder:PathOrStr=None, label_delim:str=None, valid_pct:float=0.2,
                seed:int=None, fn_col:IntsOrStrs=0, label_col:IntsOrStrs=1, suffix:str='', size=32, bs=100, shots=5, ways=20,**kwargs:Any):
        if seed:
            np.random.seed(seed)
        sampling = np.arange(df[label_col].nunique())
        np.random.shuffle(sampling)
        df[label_col] = pd.factorize(df[label_col],sort=True)[0]        
        def split_meta(self,shots,col):
            "Split the items giving the train_dl fixed number of examples of each class, while remaining go to valid_dl"
            df = self.inner_df.set_index(self.inner_df.columns[col]).reset_index()
            train_df = pd.concat([g.sample(shots,replace=False) for _,g in df.groupby(label_col)])
            train_idx = train_df.index.values
            valid_idx = np.setdiff1d(arange_of(self.items),train_idx)
            return self.split_by_idxs(train_idx,valid_idx)
        ImageList.split_meta = split_meta
        df_list = self.chunk(df,sampling,ways)   
        
        meta_train_dfs = df_list[:-int(valid_pct*len(df_list))]
        meta_train_dfs = self.reptile_df_process(meta_train_dfs)
        meta_valid_dfs = df_list[-int(valid_pct*len(df_list)):]
        self.train_tasks = [self.produce_databunch(d) for d in meta_train_dfs]
        self.valid_tasks = [self.produce_databunch(d) for d in meta_valid_dfs]

    def reptile_df_process(self,meta_train_dfs,):
        dfs = []
        for df in meta_train_dfs:
            df_list = [g[1] for g in df.groupby(df.columns[self.label_col])]
            task_list = [[d[i:i+self.shots] for i in range(0,d.shape[0],self.shots)]
                        for d in df_list]
            for i in range(len(task_list[0])):
                dfs.append(pd.concat([t[i] for t in task_list]))
        return dfs





