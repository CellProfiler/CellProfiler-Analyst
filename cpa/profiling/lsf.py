import types
import errno
import re
import random
import sys
import time
import pickle
import marshal
import os
import tempfile
import progressbar

class LSF(object):
    def __init__(self, njobs, directory=None, memory=None):
        self.njobs = njobs
        self.memory = memory
        if directory is None:
            self.directory = tempfile.mkdtemp(dir='.')
        else:
            self.directory = directory
            if not os.path.exists(self.directory):
                os.mkdir(self.directory)

    def view(self, name):
        return LSFView(self.njobs, os.path.join(self.directory, name), self.memory)


class LSFView(object):
    def __init__(self, njobs, directory=None, memory=None):
        self.njobs = njobs
        self.memory = memory
        if directory is None:
            self.directory = tempfile.mkdtemp(dir='.')
            self.resuming = False
        else:
            self.directory = directory
            self.resuming = os.path.exists(self.directory)
            if not self.resuming:
                os.mkdir(self.directory)

    def create_subdirectories(self):
        for subdir in ['new', 'tmp', 'cur', 'out', 'done', 'failed']:
            path = os.path.join(self.directory, subdir)
            os.mkdir(path)

    def start_workers(self):
        args = ['bsub']
        if self.memory:
            args.extend(['-R', 'rusage[mem=%d]' % int(self.memory)])
        args.extend(['-J', '"CPA[1-%d]"' % self.njobs, '-o', 
                     '"%s/out/j%%Ja%%I.out"' % self.directory, sys.executable,
                     '-m', 'cpa.profiling.lsf', self.directory])
        cmd = ' '.join(args)
        print cmd
        os.system(cmd)

    def list_precomputed_results(self):
        return set(int(re.match('t(\d+)\.pickle$', fn).group(1))
                   for fn in os.listdir(os.path.join(self.directory, 'done')))

    def submit_task(self, task_id, task_dict):
        basename = 't%d.pickle' % task_id
        tmp_filename = os.path.join(self.directory, 'tmp', basename)
        with open(tmp_filename, 'w') as f:
            pickle.dump(task_dict, f)
        os.rename(tmp_filename, os.path.join(self.directory, 'new', basename))

    def signal_done_submitting(self):
        # Signal that we are done submitting tasks.
        open(os.path.join(self.directory, 'submitted'), 'w').close()

    def progress(self, s, n):
        return progressbar.ProgressBar(widgets=[s, progressbar.Percentage(), 
                                                ' ', progressbar.Bar(), ' ', 
                                                progressbar.Counter(), '/', 
                                                str(n), ' ', progressbar.ETA()],
                                       maxval=n)

    def read_results(self, task_id):
        with open(os.path.join(self.directory, 'done', 't%d.pickle' % task_id)) as f:
            results = pickle.load(f)['result']
            for r in results:
                yield r

    def imap(self, function, parameters):
        if not self.resuming:
            self.create_subdirectories()
        self.start_workers()
        done_tasks = self.list_precomputed_results()
        # Divide the paramaters into batches (tasks).
        batch_size = 1 + len(parameters) // 4000
        print 'Batch size:', batch_size
        all_batches = []
        while parameters:
            all_batches.append(parameters[:batch_size])
            parameters = parameters[batch_size:]
        # Remove already-computed tasks.
        batches = [(task_id, batch)
                   for task_id, batch in enumerate(all_batches) 
                   if task_id not in done_tasks]
        # Submit tasks.
        if len(batches) > 0:
            progress = self.progress('Submitting tasks: ', len(batches))
            for task_id, batch in progress(batches):
                self.submit_task(task_id, dict(function=marshal.dumps(function.func_code), 
                                               batch=batch,
                                               task_id=task_id, attempts=3))
            self.signal_done_submitting()
        next = 0
        while True:
            try:
                npending = len(os.listdir(os.path.join(self.directory, 'new')))
                nrunning = len(os.listdir(os.path.join(self.directory, 'cur')))
            except OSError, e:
                if e.errno == errno.EIO:
                    continue
                else:
                    raise
            for fn in os.listdir(os.path.join(self.directory, 'done')):
                task_id = int(re.match('t(\d+)\.pickle$', fn).group(1))
                if task_id not in done_tasks:
                    done_tasks.add(task_id)
            # Return results
            while next in done_tasks:
                for r in self.read_results(next):
                    yield r
                next += 1
            if next == len(all_batches):
                return
            time.sleep(1)

def test_function((seconds)):
    import time
    time.sleep(seconds)
    return seconds

def test():
    view = LSFView(3, 'lsf_test')
    print view.directory
    for result in view.imap(test_function, [random.randint(1, 10)
                                            for task in range(10)]):
        print 'Task returned', result

class Worker(object):

    def __init__(self, directory, job_id, array_index):
        self.directory = directory
        self.job_id = job_id
        self.array_index = array_index
        self.start_time = time.time()

    def run(self):
        while True:
            task = self.get_task()
            if task is None:
                print 'No more tasks.'
                break
            task_id = task['task_id']
            print 'Got task', task_id
            start_time = time.time()
            try:
                code = marshal.loads(task['function'])
                function = types.FunctionType(code, globals(), "function")
                result = map(function, task['batch'])
            except:
                if task['attempts'] > 0:
                    task['attempts'] -= 1
                    with open(self.filename('cur', task_id), 'w') as f:
                        pickle.dump(task, f)
                    os.rename(self.filename('cur', task_id),
                              self.filename('new', task_id))
                else:
                    os.rename(self.filename('cur', task_id),
                              self.filename('failed', task_id))
                continue
            end_time = time.time()
            done = dict(start_time=start_time, end_time=end_time, 
                        elapsed=end_time - start_time, task_id=task_id,
                        job_id=self.job_id, array_index=self.array_index,
                        uname=os.uname(), result=result)
            with open(self.filename('tmp', task_id), 'w') as f:
                pickle.dump(done, f)
            os.rename(self.filename('tmp', task_id), self.filename('done', task_id))
            os.unlink(self.filename('cur', task_id))
            if self.is_too_old():
                print "I'm too old and will kill myself."
                break

    def filename(self, subdir, task_id):
        if subdir == 'cur':
            basename = 'j%da%dt%d' % (self.job_id, self.array_index, task_id)
        else:
            basename = 't%d.pickle' % task_id
        return os.path.join(self.directory, subdir, basename)

    def get_task(self):
        while True:
            tasks = os.listdir(os.path.join(self.directory, 'new'))
            if len(tasks) == 0:
                if os.path.exists(os.path.join(self.directory, 'submitted')):
                    return None
                else:
                    print 'Waiting for more tasks to be submitted.'
                    time.sleep(5)
                    continue
            task_basename = tasks[random.randint(0, len(tasks) - 1)]
            new_filename = os.path.join(self.directory, 'new', task_basename)
            try:
                with open(new_filename) as f:
                    task = pickle.load(f)
                task_id = task['task_id']
                # Try to claim the task by moving to a filename in the
                # cur directory that is specific to this worker.
                cur_filename = self.filename('cur', task_id)
                os.rename(new_filename, cur_filename)
                return task
            except IOError, e:
                if e.errno != errno.ENOENT:
                    raise
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise

    def is_too_old(self):
        # Finish if we have run for over an hour
        elapsed = time.time() - self.start_time 
        return elapsed >= 3600

                
if __name__ == '__main__':
    if len(sys.argv) == 2:
        directory = sys.argv[1]
        job_id = int(os.environ['LSB_JOBID'])
        array_index = int(os.environ['LSB_JOBINDEX'])
        worker = Worker(directory, job_id, array_index)
        worker.run()    
    elif len(sys.argv) == 1:
        test()


