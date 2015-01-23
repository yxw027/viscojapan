import sqlite3
import numpy as np

__all__ = ['PredDispToDatabaseWriter',
           'PredDispToDatabaseReader']

class PredDispToDatabaseWriter(object):
    def __init__(self,
                 pred_disp,
                 db_file = '~pred_disp.db',                 
                 ):
        self.pred_disp = pred_disp

        self.epochs = self.pred_disp.epochs
        self.num_epochs = len(self.epochs)
        
        self.db_file = db_file

    def create_database(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Create table        
            c.execute('''CREATE TABLE IF NOT EXISTS tb_E_cumu_slip
                         (site text,
                         day int,
                         e real,
                         n real,
                         u real,
                         PRIMARY KEY (site, day)
                         )
                         ''')

            c.execute('''CREATE TABLE IF NOT EXISTS tb_R_co
                         (site text,
                         day int,
                         e real,
                         n real,
                         u real,
                         PRIMARY KEY (site, day)
                         )
                         ''')

            c.execute('''CREATE TABLE IF NOT EXISTS tb_R_aslip
                         (site text,
                         day int,
                         e real,
                         n real,
                         u real,
                         PRIMARY KEY (site, day)
                         )
                         ''')

            c.execute('''CREATE VIEW IF NOT EXISTS view_E_co
                         AS 
                         SELECT site,e,n,u FROM tb_E_cumu_slip where day=0                         
                         ''')

            c.execute('''CREATE VIEW IF NOT EXISTS view_E_aslip
                         AS 
                         SELECT tb_E_cumu_slip.site as site,
                                tb_E_cumu_slip.day as day,
                                tb_E_cumu_slip.e - view_E_co.e as e,
                                tb_E_cumu_slip.n - view_E_co.n as n,
                                tb_E_cumu_slip.u - view_E_co.u as u
                         FROM tb_E_cumu_slip
                         JOIN view_E_co
                         ON tb_E_cumu_slip.site = view_E_co.site;
                         ''')

            c.execute('''CREATE VIEW IF NOT EXISTS view_R_cumu_slip
                         AS 
                         SELECT tb_R_co.site as site,
                                tb_R_co.day as day,
                                tb_R_co.e + tb_R_aslip.e as e,
                                tb_R_co.n + tb_R_aslip.n as n,
                                tb_R_co.u + tb_R_aslip.u as u
                         FROM tb_R_co
                         JOIN tb_R_aslip
                         ON tb_R_co.site = tb_R_aslip.site
                         AND tb_R_co.day = tb_R_aslip.day;
                         ''') 

            c.execute('''CREATE VIEW IF NOT EXISTS view_cumu_disp_added
                         AS 
                         SELECT tb_E_cumu_slip.site as site,
                                tb_E_cumu_slip.day as day,
                                tb_E_cumu_slip.e + view_R_cumu_slip.e as e,
                                tb_E_cumu_slip.n + view_R_cumu_slip.n as n,
                                tb_E_cumu_slip.u + view_R_cumu_slip.u as u
                         FROM tb_E_cumu_slip
                         JOIN view_R_cumu_slip
                         ON tb_E_cumu_slip.site = view_R_cumu_slip.site
                         AND tb_E_cumu_slip.day = view_R_cumu_slip.day;
                         ''')

            c.execute('''CREATE VIEW IF NOT EXISTS view_post_disp_added
                         AS 
                         SELECT view_E_aslip.site as site,
                                view_E_aslip.day as day,
                                view_E_aslip.e + view_R_cumu_slip.e as e,
                                view_E_aslip.n + view_R_cumu_slip.n as n,
                                view_E_aslip.u + view_R_cumu_slip.u as u
                         FROM view_E_aslip
                         JOIN view_R_cumu_slip
                         ON view_E_aslip.site = view_R_cumu_slip.site
                         AND view_E_aslip.day = view_R_cumu_slip.day;
                         ''')

            c.execute('''CREATE TABLE IF NOT EXISTS tb_cumu_disp_pred
                         (site text,
                         day int,
                         e real,
                         n real,
                         u real,
                         PRIMARY KEY (site, day)
                         )
                         ''')
            
            c.execute('''CREATE VIEW IF NOT EXISTS view_co_disp_pred
                         AS 
                         SELECT site, e, n, u
                         FROM tb_cumu_disp_pred
                         WHERE day = 0;
                         ''')
            
            c.execute('''CREATE VIEW IF NOT EXISTS view_post_disp_pred
                         AS
                         SELECT tb_cumu_disp_pred.site as site,
                                tb_cumu_disp_pred.day as day,
                                tb_cumu_disp_pred.e - view_co_disp_pred.e as e,
                                tb_cumu_disp_pred.n - view_co_disp_pred.n as n,
                                tb_cumu_disp_pred.u - view_co_disp_pred.u as u
                         FROM tb_cumu_disp_pred
                         JOIN view_co_disp_pred
                         ON tb_cumu_disp_pred.site = view_co_disp_pred.site;
                         ''')

            # Save (commit) the changes
            conn.commit()

    def _insert_into_database(self, table_name, items, duplication='REPLACE'):        
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.executemany('INSERT OR {duplication} INTO {table} VALUES (?,?,?,?,?);'\
                          .format(duplication=duplication, table=table_name),
                          items)
            conn.commit()

    def insert_total_disp_from_result(self, duplication='REPLACE'):
        items = []
        sites = self.pred_disp.sites_in_inversion
        for nth, epoch in enumerate(self.epochs):
            disps = self.pred_disp.disp_result_reader.\
                    get_cumu_pred_at_nth_epoch(nth)
    
            items += [(site, int(epoch), slip[0], slip[1], slip[2])
                     for site, slip in zip(sites, disps)]
        self._insert_into_database('tb_cumu_disp_pred', items, duplication)
        

    def insert_E_cumu_slip(self, duplication='REPLACE'):
        items = []
        sites = self.pred_disp.sites_for_prediction
        for nth, epoch in enumerate(self.epochs):
            disps = self.pred_disp.E_cumu_slip(nth).reshape([-1,3])
            items += [(site, int(epoch), slip[0], slip[1], slip[2])
                     for site, slip in zip(sites, disps)]
        self._insert_into_database('tb_E_cumu_slip', items, duplication)

    def insert_R_co(self, duplication='REPLACE'):
        items = []
        sites = self.pred_disp.sites_for_prediction
        for epoch in self.epochs:
            disps = self.pred_disp.R_co(epoch).reshape([-1,3])
            items += [(site, int(epoch), slip[0], slip[1], slip[2])
                     for site, slip in zip(sites, disps)]
        self._insert_into_database('tb_R_co', items, duplication)

    def insert_R_aslip(self, duplication='REPLACE'):
        items = []
        sites = self.pred_disp.sites_for_prediction
        for epoch in self.epochs:
            disps = self.pred_disp.R_aslip(epoch).reshape([-1,3])
            items += [(site, int(epoch), slip[0], slip[1], slip[2])
                     for site, slip in zip(sites, disps)]
        self._insert_into_database('tb_R_aslip', items, duplication)
        

    def insert_all(self, duplication='REPLACE'):
        self.insert_total_disp_from_result(duplication)
        self.insert_E_cumu_slip(duplication)
        self.insert_R_co(duplication)
        self.insert_R_aslip(duplication)

class PredDispToDatabaseReader(object):
    def __init__(self,
                 pred_db,
                 ):
        self.pred_db = pred_db

    def _select_time_series(self, site, cmpt, tb_name):
        with sqlite3.connect(self.pred_db) as conn:
            c = conn.cursor()
            tp = c.execute('select day, {cmpt} from {tb_name} where site=? order by day'\
                           .format(cmpt=cmpt, tb_name=tb_name),
                           (site,)
                           ).fetchall()
        
        ts = [ii[0] for ii in tp]
        ys = [ii[1] for ii in tp]
        return ts, ys

    def get_cumu_disp_pred(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'tb_cumu_disp_pred')

    def get_cumu_disp_added(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'view_cumu_disp_added')

    def get_post_disp_added(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'view_post_disp_added') 

    def get_post_disp_pred(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'view_post_disp_pred')

    def get_R_co(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'tb_R_co')

    def get_E_cumu_slip(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'tb_E_cumu_slip')

    def get_E_aslip(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'view_E_aslip')

    def get_R_aslip(self, site, cmpt):
        return self._select_time_series(site, cmpt, 'tb_R_aslip')

    def _select_for_all_stations(self, tb_name, epoch):
        with sqlite3.connect(self.pred_db) as conn:
            c = conn.cursor()
            tp = c.execute('select site, e, n, u from {tb_name} where day=? order by site;'\
                           .format(tb_name=tb_name),
                           (epoch,)
                           ).fetchall()
        sites = [ii[0] for ii in tp]
        ys = np.asarray([[ii[1],ii[2],ii[3]] for ii in tp])
        
        return sites, ys

    def get_R_co_at_epoch(self, epoch):
        return self._select_for_all_stations('tb_R_co', epoch)

    def get_post_disp_added_at_epoch(self, epoch):
        return self._select_for_all_stations('view_post_disp_added', epoch)

    def get_E_aslip_at_epoch(self, epoch):
        return self._select_for_all_stations('view_E_aslip', epoch)

    def get_R_aslip_at_epoch(self, epoch):
        return self._select_for_all_stations('tb_R_aslip', epoch)

    
    
            
        
        
