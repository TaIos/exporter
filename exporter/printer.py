class ExporterPrinter:

    @staticmethod
    def report(tasks, runned_tasks, logger):
        run_id = set(map(lambda x: x.id, runned_tasks))
        print(run_id)
        for t in tasks:
            if t.id in run_id:
                pass
