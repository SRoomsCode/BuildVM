# managers/task_manager.py

from concurrent.futures import (
    ThreadPoolExecutor,
    Future,
    as_completed
)

from threading import Lock

from managers.logging_manager import logger

from settings import MAX_WORKERS


class TaskManager:

    def __init__(
        self,
        max_workers=MAX_WORKERS
    ):

        self.max_workers = (
            max_workers
        )

        self.executor = (
            ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="WUM"
            )
        )

        self.tasks = {}

        self.lock = Lock()

    # ---------------------------------------------------------
    # TACHE SIMPLE
    # ---------------------------------------------------------

    def submit(
        self,
        task_name,
        func,
        *args,
        **kwargs
    ):

        future = self.executor.submit(
            func,
            *args,
            **kwargs
        )

        with self.lock:

            self.tasks[
                task_name
            ] = future

        logger.info(
            f"Tâche soumise : "
            f"{task_name}"
        )

        return future

    # ---------------------------------------------------------
    # MULTI TACHES
    # ---------------------------------------------------------

    def submit_many(
        self,
        jobs
    ):
        """
        jobs :
        [
            (
                task_name,
                func,
                args,
                kwargs
            )
        ]
        """

        futures = {}

        for (
            task_name,
            func,
            args,
            kwargs
        ) in jobs:

            future = self.submit(
                task_name,
                func,
                *args,
                **kwargs
            )

            futures[
                future
            ] = task_name

        return futures

    # ---------------------------------------------------------
    # ATTENTE
    # ---------------------------------------------------------

    def wait_all(
        self,
        futures
    ):

        results = {}

        for future in as_completed(
            futures
        ):

            task_name = futures[
                future
            ]

            try:

                results[
                    task_name
                ] = future.result()

            except Exception as exc:

                logger.error(
                    f"{task_name} : "
                    f"{exc}"
                )

                results[
                    task_name
                ] = exc

        return results

    # ---------------------------------------------------------
    # ETAT
    # ---------------------------------------------------------

    def is_running(
        self,
        task_name
    ):

        future = (
            self.tasks.get(
                task_name
            )
        )

        if future is None:

            return False

        return not future.done()

    def is_finished(
        self,
        task_name
    ):

        future = (
            self.tasks.get(
                task_name
            )
        )

        if future is None:

            return True

        return future.done()

    def get_result(
        self,
        task_name
    ):

        future = (
            self.tasks.get(
                task_name
            )
        )

        if future is None:

            return None

        if not future.done():

            return None

        return future.result()

    # ---------------------------------------------------------
    # ANNULATION
    # ---------------------------------------------------------

    def cancel_pc_job(
        self,
        pc_job
    ):

        pc_job.cancel()

    def cancel(
        self,
        task_name
    ):

        future = (
            self.tasks.get(
                task_name
            )
        )

        if not future:

            return False

        success = future.cancel()

        if success:

            logger.info(
                f"Tâche annulée : "
                f"{task_name}"
            )

        return success

    def cancel_all(
        self
    ):

        count = 0

        with self.lock:

            for future in (
                self.tasks.values()
            ):

                if future.cancel():

                    count += 1

        logger.info(
            f"{count} tâche(s) annulée(s)"
        )

        return count

    # ---------------------------------------------------------
    # INVENTAIRE
    # ---------------------------------------------------------

    def running_tasks(
        self
    ):

        items = []

        with self.lock:

            for (
                name,
                future
            ) in self.tasks.items():

                if not future.done():

                    items.append(
                        name
                    )

        return items

    def completed_tasks(
        self
    ):

        items = []

        with self.lock:

            for (
                name,
                future
            ) in self.tasks.items():

                if future.done():

                    items.append(
                        name
                    )

        return items

    # ---------------------------------------------------------
    # PURGE
    # ---------------------------------------------------------

    def cleanup(
        self
    ):

        remove = []

        with self.lock:

            for (
                name,
                future
            ) in self.tasks.items():

                if future.done():

                    remove.append(
                        name
                    )

            for name in remove:

                del self.tasks[
                    name
                ]

        if remove:

            logger.info(
                f"{len(remove)} "
                f"tâche(s) supprimée(s)"
            )

    # ---------------------------------------------------------
    # SHUTDOWN
    # ---------------------------------------------------------

    def shutdown(
        self
    ):

        logger.info(
            "Arrêt TaskManager"
        )

        self.executor.shutdown(
            wait=False,
            cancel_futures=True
        )