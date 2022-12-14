from collective.documentviewer.convert import DUMP_FILENAME
from tempfile import mkdtemp
from logging import getLogger
import os
import subprocess
import shutil


TMP_PDF_FILENAME = 'dump.pdf'
PDF_METADATA_VERSION = '1.7'

logger = getLogger(__name__)


class BaseSubProcess(object):
    default_paths = ['/bin', '/usr/bin', '/usr/local/bin']
    bin_name = ''

    if os.name == 'nt':
        close_fds = False
    else:
        close_fds = True

    def __init__(self):
        binary = self._findbinary()
        self.binary = binary
        if binary is None:
            raise IOError("Unable to find %s binary" % self.bin_name)

    def _findbinary(self):
        if 'PATH' in os.environ:
            path = os.environ['PATH']
            path = path.split(os.pathsep)
        else:
            path = self.default_paths

        for directory in path:
            fullname = os.path.join(directory, self.bin_name)
            if os.path.exists(fullname):
                return fullname

        return None

    def _run_command(self, cmd, or_error=False):
        if isinstance(cmd, basestring):
            cmd = cmd.split()
        cmdformatted = ' '.join(cmd)
        logger.info("Running command %s" % cmdformatted)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   close_fds=self.close_fds)
        output, error = process.communicate()
        process.stdout.close()
        process.stderr.close()
        if process.returncode != 0:
            error = u"""Command
%s
finished with return code
%i
and output:
%s
%s""" % (cmdformatted, process.returncode, output, error.decode('utf8'))
            logger.info(error)
            raise Exception(error)
        logger.info("Finished Running Command %s" % cmdformatted)
        if not output:
            if or_error:
                return error
        return output


class AVConvProcess(BaseSubProcess):
    if os.name == 'nt':
        bin_name = 'avconv.exe'
    else:
        bin_name = 'avconv'

    def grab_frame(self, filepath, outputfilepath, instant='00:00:5'):
        cmd = [self.binary, '-i', filepath, '-ss', instant, '-f', 'image2',
               '-vframes', '1', outputfilepath]
        self._run_command(cmd)

    def convert(self, filepath, outputfilepath):
        ext = filepath.split('.')[-1]
        if ext.lower() == 'wmv':
            cmd = [
                self.binary, '-i', filepath,
                '-map_metadata', '-1',
                '-vcodec', 'libx264', '-preset', 'ultrafast', '-profile:v',
                'baseline', '-acodec', 'aac', '-strict', 'experimental',
                '-r', '24', '-b', '255k', '-ar', '44100', '-ab', '59k',
                outputfilepath]
        if ext.lower() == 'mov':
            # files that are mov are problematic...
            # need to first converted to ogv and then back to mp4?
            # stupid, but what can you do?
            tmpoutput_path = outputfilepath.replace('.mp4', '.ogv')
            cmd = [self.binary, '-i', filepath, tmpoutput_path]
            self._run_command(cmd)
            filepath = tmpoutput_path
        if ext != 'wmv':
            cmd = [
                self.binary, '-i', filepath,
                '-vcodec', 'h264', '-acodec', 'aac', '-strict', '-2',
                outputfilepath]
        self._run_command(cmd)


class FfmpegProcess(AVConvProcess):
    if os.name == 'nt':
        bin_name = 'ffmpeg.exe'
    else:
        bin_name = 'ffmpeg'


try:
    avconv = AVConvProcess()
except IOError:
    try:
        avconv = FfmpegProcess()
    except IOError:
        avconv = None
        logger.warn('ffmpeg/avconc not installed. castle.cms will not '
                    'be able to convert video')


class ExifToolProcess(BaseSubProcess):
    """
    """
    if os.name == 'nt':
        bin_name = 'exiftool.exe'
    else:
        bin_name = 'exiftool'

    def __call__(self, filepath):
        cmd = [self.binary, '-all:all=', filepath]
        self._run_command(cmd)


try:
    exiftool = ExifToolProcess()
except IOError:
    exiftool = None
    logger.warn('exiftool not installed. castle.cms will not be able to strip metadata')  # noqa


class QpdfProcess(BaseSubProcess):
    """
    """
    if os.name == 'nt':
        bin_name = 'qpdf.exe'
    else:
        bin_name = 'qpdf'

    def __call__(self, filepath):
        outfile = '{}-processed.pdf'.format(filepath[:-4])
        cmd = [self.binary, '--linearize', '--force-version=%s' %
               PDF_METADATA_VERSION, filepath, outfile]
        self._run_command(cmd)
        shutil.copy(outfile, filepath)


try:
    qpdf = QpdfProcess()
except IOError:
    qpdf = None
    logger.warn('qpdf not installed.  Some metadata might remain in PDF files.') # noqa


class GhostScriptPDFProcess(BaseSubProcess):
    """
    """
    if os.name == "nt":
        bin_name = 'gs.exe'
    else:
        bin_name = 'gs'

    def __call__(self, filepath):
        outfile = '{}-clean.pdf'.format(filepath[:-4])
        cmd = [self.binary,
               '-q',
               '-o',
               outfile,
               '-sDEVICE=pdfwrite',
               filepath
               ]
        self._run_command(cmd)
        shutil.copy(outfile, filepath)


try:
    gs_pdf = GhostScriptPDFProcess()
except IOError:
    gs_pdf = None
    logger.warn('gs not installed. Some metadata might remain in PDF files.')


class MD5SubProcess(BaseSubProcess):
    """
    To get md5 hash of files on the filesystem so
    large files do not need to be loaded into
    memory to be checked
    """
    if os.name == 'nt':
        bin_name = 'md5.exe'
    else:
        bin_name = 'md5'

    def __call__(self, filepath):
        cmd = [self.binary, filepath]
        hashval = self._run_command(cmd)
        return hashval.split('=')[1].strip()


try:
    md5 = MD5SubProcess()
except IOError:
    md5 = None


class MD5SumSubProcess(BaseSubProcess):
    """
    To get md5 hash of files on the filesystem so
    large files do not need to be loaded into
    memory to be checked
    """
    if os.name == 'nt':
        bin_name = 'md5sum.exe'
    else:
        bin_name = 'md5sum'

    def __call__(self, filepath):
        cmd = [self.binary, filepath]
        hashval = self._run_command(cmd)
        return hashval.split('  ')[0].strip()


try:
    if md5 is None:
        md5 = MD5SumSubProcess()
except IOError:
    logger.exception("No md5sum or md5 installed. castle.cms "
                     "will not be able to detect md5 of files.")
    md5 = None


class DocSplitSubProcess(BaseSubProcess):
    """
    idea of how to handle this shamelessly
    stolen from ploneformgen's gpg calls
    """

    if os.name == 'nt':
        bin_name = 'docsplit.exe'
    else:
        bin_name = 'docsplit'

    def dump_image(self, data, size, _format):
        # docsplit images pdf.pdf --size 700x,300x,50x
        # --format gif --output
        tmpdir = mkdtemp()
        tmpfilepath = os.path.join(tmpdir, TMP_PDF_FILENAME)
        tmpfi = open(tmpfilepath, 'wb')
        tmpfi.write(data)
        tmpfi.close()
        cmd = [
            self.binary, "images", tmpfilepath,
            '--language', 'eng',
            '--size', size,
            '--format', _format,
            '--output', tmpdir,
            '--pages', '1']

        self._run_command(cmd)
        os.remove(tmpfilepath)
        return os.path.join(tmpdir, 'dump_1.gif')

    def convert_to_pdf(self, filepath, filename, output_dir):
        # get ext from filename
        ext = os.path.splitext(os.path.normcase(filename))[1][1:]
        inputfilepath = os.path.join(output_dir, 'dump.%s' % ext)
        shutil.move(filepath, inputfilepath)
        orig_files = set(os.listdir(output_dir))
        cmd = [
            self.binary, 'pdf', inputfilepath,
            '--output', output_dir]
        self._run_command(cmd)

        # remove original
        os.remove(inputfilepath)

        # while using libreoffice, docsplit leaves a 'libreoffice'
        # folder next to the generated PDF, removes it!
        libreOfficePath = os.path.join(output_dir, 'libreoffice')
        if os.path.exists(libreOfficePath):
            shutil.rmtree(libreOfficePath)

        # move the file to the right location now
        files = set(os.listdir(output_dir))

        if len(files) != len(orig_files):
            # we should have the same number of files as when we first began
            # since we removed libreoffice.
            # We do this in order to keep track of the files being created
            # and used...
            raise Exception("Error converting to pdf")

        converted_path = os.path.join(output_dir,
                                      [f for f in files - orig_files][0])
        shutil.move(converted_path, os.path.join(output_dir, DUMP_FILENAME))


try:
    docsplit = DocSplitSubProcess()
except IOError:
    logger.exception("No docsplit installed.")
    docsplit = None
