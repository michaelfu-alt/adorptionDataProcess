# controller/sample_manager.py
# ① 样品的增删改查
# 	•	_load_sample_list
# 	•	_load_sample_details
# 	•	copy_samples
# 	•	paste_samples
# 	•	_clone_sample_from_external_db
# 	•	delete_sample
# 	•	edit_sample
# 	•	_on_edit_save
# 	•	find_duplicates
# 	•	_on_delete_duplicates
# 	•	define_sample_set
# 	•	compare_sample_sets
# 	•	_show_comparison_plot
# 	•	on_tree_select
# 	•	trace_samples

# ② 其它跟样品操作相关的状态变量
# 	•	self.sample_sets
# 	•	self._copied_samples
# 	•	self._copied_db_path

# •	所有直接涉及样品信息、操作的函数都迁移到 sample_manager.py。
# •	迁移过程中只需要将 self.model, self.view 替换为 self.controller.model/self.controller.view。
# •	若涉及到其它 manager 之间的协作，可在 manager 的 __init__ 里保存 main_controller 的引用。


class SampleManager:
    def __init__(self, main_controller):
        self.controller = main_controller  # 可用于访问主 controller 的 model/view

        # 迁移以下属性（可在主controller.__init__中赋值）
        self.sample_sets = {}
        self._copied_samples = []
        self._copied_db_path = None


    def delete_sample(self):
        sels = self.view.sample_tree.selection()
        if not sels:
            # 弹窗
            return
        names = [self.view.sample_tree.item(i, "values")[0] for i in sels]
        confirm = ... # 弹窗确认
        if not confirm:
            return
        for name in names:
            try:
                self.model.delete_sample(name)  # 调用model
            except Exception as e:
                # 错误弹窗
                pass
        self._load_sample_list()
        # 弹窗提示完成

    def edit_sample(self):
        # 打开编辑弹窗等, 调用_on_edit_save
        pass

    def _on_edit_save(self, sample_name, updated_info):
        try:
            self.model.update_sample_info(sample_name, updated_info)
            self._load_sample_list()
            # 刷新右侧详情
        except Exception as e:
            # 弹窗提示
            pass

    def find_duplicates(self):
        # 1. 弹窗让用户选字段
        # 2. 调用self.model.find_duplicates(fields)
        # 3. 显示结果并可操作
        pass

    def _on_delete_duplicates(self, to_delete: list[str]):
        for name in to_delete:
            try:
                self.model.delete_sample(name)
            except Exception as e:
                pass
        self._load_sample_list()
        # 弹窗提示


        
    def load_sample_list(self):
        """Fetch sample overview and populate the Treeview table."""
        try:
            rows = self.controller.model.get_sample_overview()
            self.controller.view.populate_sample_table(rows)
        except Exception as e:
            self.controller.view.messagebox.showerror("Load Error", f"Could not load sample list:\n{e}")

    def load_sample_details(self, name):
        try:
            info = self.controller.model.get_sample_info(name)
            results = self.controller.model.get_sample_results(name)
            ads, des = self.controller.model.get_adsorption_data(name)
            self.controller.view.update_sample_info(info)
            self.controller.view.update_result_summary(results)
            self.controller.view.update_data_table(ads, des)
            self.controller.view.update_plot(ads, des)
            self.controller.view.update_psd_table(name)
            self.controller.view.update_psd_plot(name)
        except Exception as e:
            self.controller.view.messagebox.showerror("Load Error", f"Failed to load sample '{name}':\n{e}")

    def on_tree_select(self, event):
        sels = self.controller.view.sample_tree.selection()
        if not sels:
            return
        idx_map = {iid: self.controller.view.sample_tree.index(iid) for iid in sels}
        top_iid = min(idx_map, key=idx_map.get)
        name = self.controller.view.sample_tree.item(top_iid, 'values')[0]
        self.load_sample_details(name)

    def copy_samples(self):
        print("DEBUG: Inside copy_samples()")
        if not self._copied_samples:
            self.controller.view.messagebox.showinfo("Copy Samples", "No samples selected to copy.")
            return
        self.controller.view.set_status(f"Copied {len(self._copied_samples)} sample(s).")

    def paste_samples(self):
        """
        If self._copied_db_path == self.model.db_path:
            → clone within the same DB (old behavior).
        Else:
            → “cross‐DB clone”:
            1) Open a temporary DatabaseModel on the old DB file.
            2) Fetch all data for each copied sample_name from that external DB.
            3) Insert those rows into the current DB under a new unique name.
        """
        print("DEBUG: paste_samples() called.")
        print("  _copied_samples =", self._copied_samples)
        print("  _copied_db_path =", self._copied_db_path)
        print("  current model.db_path =", self.model.db_path)

        if not self._copied_samples or not self._copied_db_path:
            self.messagebox.showinfo("Paste Samples", "No samples in clipboard.")
            return

        pasted_names = []
        current_db = self.model.db_path
        source_db  = self._copied_db_path

        # Add a quick check: do these paths match exactly?
        import os
        same_db = os.path.abspath(source_db) == os.path.abspath(current_db)
        print(f"  same_db? {same_db} (source: {source_db}, current: {current_db})")

        for old_name in self._copied_samples:
            try:
                if same_db:
                    print(f"  → cloning '{old_name}' within the same DB")
                    new_name = self.model.clone_sample(old_name)
                else:
                    print(f"  → cloning '{old_name}' from external DB '{source_db}'")
                    new_name = self._clone_sample_from_external_db(source_db, old_name)

                pasted_names.append(new_name)
            except Exception as e:
                # Show the exact exception message in the console:
                print(f"ERROR: Could not paste '{old_name}': {e}")
                self.messagebox.showerror(
                    "Paste Error",
                    f"Could not paste '{old_name}': {e}"
                )
                continue

        if pasted_names:
            self._load_sample_list()
            self.messagebox.showinfo(
                "Paste Complete",
                f"Pasted {len(pasted_names)} sample(s):\n" +
                "\n".join(pasted_names)
            )
            self.view.set_status(f"Pasted {len(pasted_names)} sample(s).")

        # Clear the copied buffer so that repeated “Paste” without a new “Copy” does nothing
        self._copied_samples  = []
        self._copied_db_path  = None

    def delete_sample(self):
        # ...完整迁移你的删除样品逻辑...
        pass

    def edit_sample(self):
        # ...完整迁移你的编辑样品逻辑...
        pass

    def _on_edit_save(self, sample_name, updated_info):
        # ...完整迁移你的编辑保存逻辑...
        pass

    def find_duplicates(self):
        # ...完整迁移你的查重逻辑...
        pass

    def _on_delete_duplicates(self, to_delete: list[str]):
        # ...完整迁移你的查重删除逻辑...
        pass

    def define_sample_set(self):
        # ...完整迁移你的样品集合定义逻辑...
        pass

    def compare_sample_sets(self):
        # ...完整迁移你的样品集合对比逻辑...
        pass

    def _show_comparison_plot(self, field, set_names):
        # ...完整迁移你的样品集合对比画图逻辑...
        pass

    def trace_samples(self):
        # ...完整迁移你的trace样品逻辑...
        pass