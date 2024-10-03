import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re
from typing import Optional, Union
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from market_research.scraper._visualization_scheme import BaseVisualizer
import plotly.graph_objects as go  

class Rvisualizer(BaseVisualizer):

    def __init__(self, df:None, output_folder_path="results", maker_filter=None):
        super().__init__(output_folder_path=output_folder_path)
        self.output_folder_path =output_folder_path
        
        if df is None:
            json_path = 'https://raw.githubusercontent.com/xikest/research_market_tv/main/json/measurement_data.json'
            self.df = pd.read_json(json_path, orient='records', lines=True)
        else:
            self.df = df.copy()        
        self.data_detail_dict: dict = {}
        self.data_detail_df = None
        self.title_units_dict = {
            "HDR Brightness": "cd/m²",
            "SDR Brightness": "cd/m²",
            "Black Frame Insertion (BFI)": "Hz",
            "Black Uniformity": "%",
            "Color Gamut": "%",
            "Color Volume": "cd/m²",
            "Color Volume(ITP)": "%",
            "Flicker-Free": "Hz",
            "Gray Uniformity": "%",
            "HDR Brightness In Game Mode": "cd/m²",
            "Reflections": "%",
            "Response Time": "ms",
            "Stutter": "ms",
            "Variable Refresh Rate": "Hz",
            "Viewing Angle": "°"
        }
        self.df = self._initialize_data(self.df)
        
        if maker_filter is not None:
            if isinstance(maker_filter, str):
                maker_filter = [maker_filter]
            
            filtered_mask = self.df['maker'].isin(maker_filter)
            if filtered_mask.sum() > 0:
                self.df = self.df[filtered_mask]


    def _initialize_data(self, df):
        
        def retrim(ds: pd.Series, mark: str = ","):
            return ds.str.replace(mark, "")
        
        df.loc[df['label'] == '1,000 cd/m² DCI P3 Coverage ITP', 'header'] = 'Color Volume(ITP)'
        df.loc[df['label'] == '10,000 cd/m² Rec 2020 Coverage ITP', 'header'] = 'Color Volume(ITP)'
        df.loc[df['label'] == 'Contrast', 'label'] = 'Contrast_'
        label_dict = {'1,000 cd/m² DCI P3 Coverage ITP': "DCI",
                      '10,000 cd/m² Rec 2020 Coverage ITP': "BT2020",
                      'Blue Luminance': "Blue",
                      'Cyan Luminance': "Cyan",
                      'Green Luminance': "Green",
                      'Magenta Luminance': "Magenta",
                      'Red Luminance': "Red",
                      'White Luminance': "White",
                      'Yellow Luminance': "Yellow"}

        value_dict = {"N/A": "0", "Inf ": "1000000"}

        for target, label in label_dict.items():
            df.loc[:, "label"] = df.label.map(lambda x: x.replace(target, label))
        for target, value in value_dict.items():
            df.loc[:, "result_value"] = df.result_value.map(lambda x: x.replace(target, value))

        trim_marks = ["cd/m²", ",", "%", "°", "K", "ms", "Hz", "dB", ": 1"]
        for trim_mark in trim_marks:
            try:
                df.loc[:, "result_value"] = retrim(df["result_value"], trim_mark)
            except:
                pass

        df = df[(df['category'] != 'Sound Quality') & (df['category'] != 'Smart Features') & (df['category'] != 'Inputs')]
        df = df[~df.score.isin([""])]  # score가 있는 데이터만 사용
        df['result_value'] = df['result_value'].astype(float)
        df["score"] = df.score.astype(float)
        return df









    def plotsns_facet_bar(self, column: str, col_wrap=3, height=4, facet_yticks: Optional[Union[dict, list]] = None,
                          facet_ylims: Optional[Union[dict, list]] = None, show_annot=True,
                          swap_mode: bool = False, save_plot_name:str=None):
        def get_data(column):
            
            def set_data_detail(column: str = None):
                
                def brightness_trim(df):
                    df_peak = df[df['label'].str.contains("Window") & df['label'].str.contains("Peak")]
                    df_peak.loc[:, "label"] = df_peak["label"].map(lambda x: int(x.split("%")[0].split(" ")[-1]))

                    df_peak = df_peak.sort_values(["model", "label"], ascending=True)
                    df_peak["label"] = df_peak.label.map(lambda x: str(x) + "%")
                    df_peak = df_peak.rename(columns={"label": "APL"})
                    return df_peak
                
                self._target_column = column
                data_df = self.df[self.df["header"] == column]
                data_df = data_df.sort_values(["maker", "product", "label"], ascending=False)
                data_df = data_df.pivot(index=["maker", "product"], columns="label", values='result_value')
                data_df.columns = data_df.columns.map(lambda x: str(x))
                data_df = data_df.reset_index()
                data_df.loc[:, 'model'] = data_df['maker'] + '_' + data_df['product']
                data_df = data_df.drop(["maker", "product"], axis=1)

                data_df = data_df.melt(id_vars=['model'], var_name='label', value_name=column)

                if "brightness" in column.lower():
                    data_df = brightness_trim(data_df)

                return data_df
            
            data_df = self.data_detail_dict.get(column)

            if data_df is None:
                data_df = set_data_detail(column)
                self.data_detail_dict.update({column: data_df})
                data_df = self.data_detail_dict.get(column)
            return data_df


        df = get_data(column)
        mode_dict = self._plot_mode(column, swap_mode)
        col_y = mode_dict.get("col_y")
        col_x = mode_dict.get("col_x")
        col_facet = mode_dict.get("col_facet")

        color_palette = sns.color_palette("Set2", n_colors=len(set(df[col_x])))

        sns.set(style="whitegrid")
        g = sns.FacetGrid(df, col=col_facet, col_wrap=col_wrap, height=height, sharey=False, sharex=False)
        g.map_dataframe(sns.barplot, x=col_x, y=col_y, hue=col_x, palette=color_palette, )
        g.set_axis_labels(col_x, col_y)

        if facet_yticks:
            if isinstance(facet_yticks, dict):
                for idx, ytick in facet_yticks.items():
                    g.axes.flat[int(idx)].yaxis.set_ticks(ytick)
            elif isinstance(facet_yticks, list):
                for ax in g.axes.flat:
                    ax.yaxis.set_ticks(facet_yticks)

        if facet_ylims:
            if isinstance(facet_ylims, dict):
                for idx, ylim in facet_ylims.items():
                    g.axes.flat[idx].set(ylim=ylim)
            elif isinstance(facet_ylims, tuple):
                for ax in g.axes.flat:
                    ax.set(ylim=facet_ylims)

        # g.set_xticklabels(rotation=90, horizontalalignment='right')
        for ax in g.axes.flat:
            for label in ax.get_xticklabels():

                if len(label.get_text()) > 5:
                    label.set_rotation(90)
                    label.set_horizontalalignment('right')
                else:
                    label.set_rotation(0)


        suffix = self.title_units_dict.get(col_y)
        if suffix is not None:
            sup_title = f"{col_y} ({suffix}) by {col_x}"
        else:
            sup_title = f"{col_y} by {col_x}"

        g.fig.suptitle(sup_title, y=1.05)
        g.fig.subplots_adjust(top=1)

        if show_annot:
            for ax in g.axes.flat:
                for p in ax.patches:
                    height_val = p.get_height()
                    annot_text = f'{height_val:.0f}' if height_val.is_integer() else f'{height_val}'
                    if height_val >= 10000:
                        annot_text = f'{height_val / 1000:.1f}K'
                    ax.annotate(annot_text, (p.get_x() + p.get_width() / 2., height_val), ha='center', va='center',
                                xytext=(0, 1), textcoords='offset points', fontsize=8)
                ax.yaxis.set_ticks([])
        sns.despine()
        plt.tight_layout()

        if save_plot_name is None:
            file_name = re.sub(r'\([^)]*\)', '', sup_title)
            save_plot_name = f"plot_for_{file_name}.png"
        plt.savefig(self.output_folder / save_plot_name, bbox_inches='tight')
        plt.show()

    import matplotlib.pyplot as plt

    def plot_lines(self, column, swap_mode=True, ylims: list = None,
                   yticks: list = None, save_plot_name: str = None):

        df = self._get_data(column)
        mode_dict = self._plot_mode(column, swap_mode)
        col_y = mode_dict.get("col_y")
        col_x = mode_dict.get("col_x")
        col_color = mode_dict.get("col_facet")

        suffix = self.title_units_dict.get(col_y)

        if suffix is not None:
            sup_title = f"{col_y} ({suffix}) by {col_x}"
        else:
            sup_title = f"{col_y} by {col_x}"

        fig, ax = plt.subplots(figsize=(10, 5))

        if col_color is not None:
            colors = plt.cm.viridis(np.linspace(0, 1, len(df[col_color].unique())))
            for i, (group, data) in enumerate(df.groupby(col_color)):
                ax.plot(data[col_x], data[col_y], label=group, color=colors[i])
                for x, y, val in zip(data[col_x], data[col_y], data[col_y]):
                    ax.annotate(f'{val}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center')
        else:
            ax.plot(df[col_x], df[col_y])
            for x, y, val in zip(df[col_x], df[col_y], df[col_y]):
                ax.annotate(f'{val}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center')

        ax.set_title(sup_title)
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)

        if yticks is not None:
            ax.set_yticks(yticks)
        if ylims is not None:
            ax.set_ylim(ylims)

        if save_plot_name is None:
            file_name = re.sub(r'\([^)]*\)', '', sup_title)
            save_plot_name = f"plot_for_{file_name}.png"
        plt.savefig(save_plot_name)
        plt.show()


    def _plot_mode(self, column, swap_mode):
        col_y = column
        col_x = "model"
        col_facet = "label"

        if "brightness" in col_y.lower():
            col_x = "model"
            col_facet = "APL"

        if swap_mode == True:
            temp = col_x
            col_x = col_facet
            col_facet = temp

        return {"col_y": col_y,
                "col_x": col_x,
                "col_facet": col_facet}



    def radar_scores(self, return_fig: bool = False):
        col_socres = ["maker", "year", "series", "category", "header", "score"]
        data_df = self.df[col_socres].drop_duplicates().replace("", np.nan).dropna()
        
        data_df['year'] = data_df['year'].astype(int).astype(str)
        data_df["score"] = data_df["score"].map(lambda x: float(x))
        data_df = data_df.pivot(index=["maker", "year", "series"], columns=["category", "header"], values='score')
        data_df = data_df.T.reset_index().sort_index(axis=1, level=0).drop("category", axis=1).set_index("header")
        data_df = data_df.sort_index(axis='columns', level=[0, 1, 2], ascending=[True, False, False])


        data_df = data_df.loc[
            ['Black Uniformity', 'Contrast', 'SDR Brightness', 'HDR Brightness',
            'Color Volume', 'Color Gamut', 'Viewing Angle', 'Reflections',
            'Pre Calibration', 'Gray Uniformity', 'Response Time',
            'HDR Native Gradient', 'PQ EOTF Tracking'], :
        ]

        # Plotly Figure 생성
        fig = go.Figure()

        years = data_df.columns.get_level_values(1).unique()
        years = sorted(years, reverse=True)
        series_group = data_df.columns.get_level_values(2).unique()
        

        for series in series_group:
                data_series = data_df.xs((series), level=(2), axis=1)
                year = data_series.columns.get_level_values(1).unique().item()
                maker = data_series.columns.get_level_values(0).unique().item()

                values = data_series.mean(axis=1).values.flatten()
                values = np.concatenate((values, [values[0]]))
                theta = data_df.index.tolist() + [data_df.index[0]]
                fill_color = f'rgba({np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {np.random.randint(0, 255)}, 0.25)'

                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=theta,
                    fill='toself',
                    fillcolor=fill_color,
                    name=f"{maker} {series}({year})",  # Series 이름에 연도 포함
                    mode='lines',
                    line=dict(color=fill_color, width=2),
                    visible= True  
                ))


        year_dropdown = dict(
            active=0,  
            buttons=[
                dict(
                    label='All',  
                    method='update',
                    args=[
                        {'visible': [True] * len(fig.data)}
                    ]
                )
            ] + [
                dict(
                    label=year,
                    method='update',
                    args=[
                        {'visible': [year in trace.name for trace in fig.data]}
                    ]
                ) for year in years
            ]
        )
    

        # 레이아웃 업데이트
        fig.update_layout(
            updatemenus=[{
                'buttons': year_dropdown['buttons'],
                'direction': 'down',
                'showactive': True,
                'x': 0,  # 가로 위치 (0~1)
                'y': 1.0,  # 세로 위치 (0~1) - 값을 조정하여 메뉴 위치 조정
                'yanchor': 'bottom'  # 기준점 설정
            }]
        )

        # 레이아웃 설정
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=False,
                    showline=False,
                    range=[0, 10],
                ),
                angularaxis=dict(
                    visible=True,
                    showline=True,
                    linecolor='gray',
                    linewidth=0.5,
                )
            ),
            showlegend=True,
            legend=dict(
                x=1.3,
                y=0.5,
                traceorder='normal',
                font=dict(size=12, family='Arial, sans-serif'),
            ),
            width=1000,
            height=800,
            font=dict(size=10, family='Arial, sans-serif', weight='bold'),
            margin=dict(l=80, r=100, t=10, b=10),
        )

        fig.write_html(self.output_folder / "radar_plot.html")
        if return_fig:
            return fig
        else:
            fig.show()  # 그래프 보여주기


 
    def heatmap_scores(self, cmap="cividis"):
        col_socres = ["maker","year", "series", "category", "header", "score"]
        
        data_df = self.df[col_socres].drop_duplicates().replace("", np.nan).dropna()
        data_df["score"] = data_df["score"].map(lambda x: float(x))
        # data_df["product"] = data_df["product"].map(lambda x: x.replace("-oled", ""))
        data_df = data_df.pivot(index=["maker","year", "series"], columns=["category", "header"], values='score')
        # data_df = data_df.T.reset_index().sort_index(axis=1).drop("category", axis=1).set_index("header")
        data_df = data_df.T.reset_index().sort_index(axis=1, level=0).drop("category", axis=1).set_index("header")
        data_df = data_df.sort_index(axis=1, level=[0, 1])  # Sort the index levels
    

        x_labels = ['-'.join(map(str, idx)) for idx in data_df.columns]
        fig = go.Figure(data=go.Heatmap(
            z=data_df.values,  # 데이터 값
            x=x_labels,  # x축 레이블
            y=data_df.index,    # y축 레이블
            colorscale=cmap,     # 색상 맵
            showscale=False,
            zmin=0,              # 최소 값
            zmax=10,             # 최대 값
            text=data_df.values, # 각 셀의 텍스트로 데이터 값 표시
            texttemplate="%{text:.1f}",  # 텍스트 형식 지정
            hoverinfo='none'     # 호버 시 텍스트 정보 표시 안 함
        ))

        # 제목 설정
        fig.update_layout(
            title='Rtings Score heatmap',
            xaxis=dict(tickangle=90),
            yaxis=dict(tickangle=0),
            # width=1000,  # 그래프 너비
            height=1200,   # 그래프 높이
            font=dict(size=16, family='Arial, sans-serif', weight='bold'),
            margin=dict(l=300, r=20, t=40, b=300), 
        )

        # fig.write_html(self.output_folder/f"{self.plot_name}_heatmap.html")
        
        fig.show()
                
        # if return_fig:
        #     return fig
        # else:
        #     fig.show()  # 그래프 보여주기
        

    def plot_pca(self, figsize=(10, 6), title="Principal component", palette="RdYlBu", save_plot_name:str=None):
        sns.set_theme(style="whitegrid")
        ddf = self.df.copy()
        ddf['category_header_label'] = ddf['category'] + '_' + ddf['header'] + '_' + ddf['label']
        ddf['maker_product'] = ddf['maker'] + '_' + ddf['product']
        ddf = ddf.drop(["category", "header", "label", "score", "maker", "product"], axis=1)[
            ddf.category.isin(["Picture Quality"])]
    
        ddf_pivot = ddf.pivot_table(index=['maker_product'], columns=['category_header_label'],
                                    values=['result_value'],
                                    aggfunc={'result_value': 'first'})
        scaler = StandardScaler()
        X_numeric_scaled = scaler.fit_transform(ddf_pivot)
    
        pca = PCA(n_components=0.8)  # Set explained variance threshold to 0.8
        X_pca = pca.fit_transform(X_numeric_scaled)
    
        label_pc = [f"PC{i + 1}: {var*100:.2f}%" for i, var in enumerate(pca.explained_variance_ratio_)]

        pca_result_df = (
            pd.DataFrame(np.round(pca.components_.T * np.sqrt(pca.explained_variance_), 4),
                         columns=label_pc, index=ddf_pivot.columns)
            .reset_index()
            .assign(category=lambda x: x["category_header_label"].str.split("_").str[0],
                    header=lambda x: x["category_header_label"].str.split("_").str[1],
                    label=lambda x: x["category_header_label"].str.split("_").str[2])
            .drop("category_header_label", axis=1)
        )

        pca_result_by_header_df = pca_result_df.groupby(["header"])[label_pc].mean().reset_index()
        pca_result_by_header_df = pca_result_by_header_df.sort_values(by=label_pc[0], ascending=False)
        pca_result_long_df = pd.melt(pca_result_by_header_df, id_vars=["header"], var_name="Principal Component",
                                     value_name="loading")
    
        # 그래프 생성
        plt.figure(figsize=figsize)
        sns.barplot(x="loading", y="header", hue="Principal Component", data=pca_result_long_df, palette=palette)
        plt.xlim(-1, 1)
        plt.title(label=title, y=1.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), fancybox=True, shadow=False, ncol=3)
    
        plt.tight_layout()
        sns.despine()
        if save_plot_name is None:
            save_plot_name = f"plot_pca_for_{title}.png"
        plt.savefig(self.output_folder / save_plot_name, bbox_inches='tight')
        plt.show()

