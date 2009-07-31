#(ie. use with rpm --rebuild):
#
#	--with debug	Compile with debugging code
# 
#  enable build with debugging code: will _not_ strip away any debugging code,
#  will _add_ -g3 to CFLAGS, will _add_ --enable-maintainer-mode to 
#  configure.

%define build_debug 0
%define build_test 0

# commandline overrides:
# rpm -ba|--rebuild --with 'xxx'
%{?_with_debug: %{expand: %%global build_debug 1}}
%{?_without_debug: %{expand: %%global build_debug 0}}
%{?_with_test: %{expand: %%global build_test 1}}
%{?_without_test: %{expand: %%global build_test 0}}

%if %{build_debug}
# disable build root strip policy
%define __spec_install_post %{_libdir}/rpm/brp-compress || :

# This gives extra debuggin and huge binaries
%{expand:%%define optflags %{optflags} %([ ! $DEBUG ] && echo '-g3')}
%endif

%if %{build_debug}
%define build_test 1
%define build_debug 1
%endif

%define _requires_exceptions perl(Data::Flow)\\|perl(Carp::Heavy)\\|perl(Apache::FunctionTable)\\|perl(Apache::StructureTable)\\|perl(Data::Flow)\\|perl(Module::Build)\\|perl(Apache::TestConfigParse)\\|perl(Apache::TestConfigPerl)

#Module-Specific definitions
%define apache_version 2.2.8
%define mod_name mod_perl
%define mod_conf 75_%{mod_name}.conf
%define mod_so %{mod_name}.so
%define perl_version %(rpm -q --qf '%%{epoch}:%%{version}' perl)

Summary:	An embedded Perl interpreter for the apache Web server
Name:		apache-%{mod_name}
Version:	2.0.4
Release:	%mkrel 8
Group:		System/Servers
License:	Apache License
URL:		http://perl.apache.org/
Source0:	http://perl.apache.org/dist/%{mod_name}-%{version}.tar.gz
Source1:	http://perl.apache.org/dist/%{mod_name}-%{version}.tar.gz.asc
Source2:	%{mod_conf}
Source3:	apache-mod_perl-testscript.pl
Patch0:		mod_perl-external_perl-apache-test.diff
Patch1:         mod_perl-2.0.4-inline.patch
Patch2:		mod_perl-format-string.patch
Patch3:		mod_perl-2.0.x-CVE-2009-0796.diff
Requires:       perl = %{perl_version}
BuildRequires:	perl-devel >= 5.8.2
BuildRequires:	perl-Apache-Test >= 1.29
%if %{build_test}
BuildRequires:	perl-CGI >= 1:3.08
BuildRequires:	perl-HTML-Parser
BuildRequires:	perl-libwww-perl
BuildRequires:	perl-Tie-IxHash
BuildRequires:	perl-URI
BuildRequires:	perl-BSD-Resource
BuildRequires:	apache-conf >= %{apache_version}
BuildRequires:	apache-mpm-prefork >= %{apache_version}
BuildRequires:	apache-base >= %{apache_version}
BuildRequires:	apache-modules >= %{apache_version}
BuildRequires:	apache-mod_cache >= %{apache_version}
BuildRequires:	apache-mod_dav >= %{apache_version}
BuildRequires:	apache-mod_deflate >= %{apache_version}
BuildRequires:	apache-mod_disk_cache >= %{apache_version}
BuildRequires:	apache-mod_file_cache >= %{apache_version}
BuildRequires:	apache-mod_ldap >= %{apache_version}
BuildRequires:	apache-mod_mem_cache >= %{apache_version}
BuildRequires:	apache-mod_proxy >= %{apache_version}
BuildRequires:	apache-mod_ssl >= %{apache_version}
BuildRequires:	apache-mod_suexec >= %{apache_version}
BuildRequires:	apache-mod_userdir >= %{apache_version}
%endif
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):  apache-conf >= %{apache_version}
Requires(pre):  apache-mpm-prefork >= %{apache_version}
Requires(pre):  apache-base >= %{apache_version}
Requires(pre):  apache-modules >= %{apache_version}
Requires:	apache-conf >= %{apache_version}
Requires:	apache-mpm-prefork >= %{apache_version}
Requires:	apache-base >= %{apache_version}
Requires:	apache-modules >= %{apache_version}
BuildRequires:	apache-devel >= %{apache_version}
Epoch:		1
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
%{name} incorporates a Perl interpreter into the apache web server,
so that the Apache web server can directly execute Perl code.
Mod_perl links the Perl runtime library into the apache web server and
provides an object-oriented Perl interface for apache's C language
API.  The end result is a quicker CGI script turnaround process, since
no external Perl interpreter has to be started.

Install %{name} if you're installing the apache web server and you'd
like for it to directly incorporate a Perl interpreter.

You can build %{name} with some conditional build swithes;

(ie. use with rpm --rebuild):
    --with[out] debug	Compile with debugging code (forces --with test)
    --with[out]	test	Initiate a Apache-Test run

%package	devel
Summary:	Files needed for building XS modules that use mod_perl
Group:		Development/C
Requires:	%{name} = 1:%{version}
Requires:	apache-devel >= %{apache_version}
Epoch:		1

%description	devel 
The mod_perl-devel package contains the files needed for building XS
modules that use mod_perl.

%prep

%setup -q -n %{mod_name}-%{version}
%patch0 -p1
%patch1 -p1 -b .inline
%patch2 -p1
%patch3 -p0

rm -rf Apache-Test

cp %{SOURCE2} %{mod_conf}

for i in `find . -type d -name .svn`; do
    if [ -e "$i" ]; then rm -rf $i; fi >&/dev/null
done

%build

# Compile the module.
%{__perl} Makefile.PL \
%if %{build_debug}
    MP_MAINTAINER=1 \
    MP_TRACE=1 \
    MP_CCOPTS="$(%{_sbindir}/apxs -q CFLAGS) -g3 -Werror -fPIC" \
%else
    MP_CCOPTS="$(%{_sbindir}/apxs -q CFLAGS) -fPIC" \
%endif
    MP_APXS=%{_sbindir}/apxs \
    MP_APR_CONFIG=%{_bindir}/apr-1-config \
    INSTALLDIRS=vendor </dev/null 

ln -s Apache-mod_perl_guide-1.29/bin bin

%make

# XXX mod_include/SSI does not include files when they are not named .shtml
mv t/htdocs/includes-registry/test.pl t/htdocs/includes-registry/test.shtml
mv t/htdocs/includes-registry/cgipm.pl t/htdocs/includes-registry/cgipm.shtml
sed 's/\.pl/.shtml/' t/htdocs/includes/test.shtml > tmpfile && mv tmpfile t/htdocs/includes/test.shtml

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%if %{build_debug}
export DONT_STRIP=1
%endif

%if %{build_test}
# Run the test suite.
#  Need to make t/htdocs/perlio because it isn't expecting to be run as
#  root and will fail tests that try and write files because the server
#  will have changed it's uid.
mkdir -p t/htdocs/perlio
chmod 777 t/htdocs/perlio

#
# fix for bad_scripts.t in 1.99_12
# [Tue Mar 02 17:28:26 2004] [error] file permissions deny server execution/usr/src/packages/BUILD/modperl-2.0/ModPerl-Registry/t/cgi-bin/r_inherited.pl
if test -e ModPerl-Registry/t/cgi-bin/r_inherited.pl; then chmod +x ModPerl-Registry/t/cgi-bin/r_inherited.pl; fi
#
# 1.99_12_20040302 fix for t/hooks/cleanup.t and t/hooks/cleanup2.t
# [Tue Mar 02 18:38:41 2004] [error] [client 127.0.0.1] can't open /usr/src/packages/BUILD/modperl-2.0/t/htdocs/hooks/cleanup2: Permission denied at /usr/src/packages/BUILD/modperl-2.0/Apache-Test/lib/Apache/TestUtil.pm line 82.
mkdir -p t/htdocs/hooks
chmod 2770 t/htdocs/hooks
#
# run test suite:
#
#make TEST_VERBOSE=1 APACHE_TEST_PORT=select APACHE_TEST_STARTUP_TIMEOUT=360 test  || {
#       ps aufx | grep "/usr/sbin/httpd-prefork -d /usr/src/packages/BUILD/modperl-2.0" \
#               | grep -v grep | awk '{print $2}' | xargs -r kill
#       exit 1
#}
perl t/TEST -start-httpd -port select -startup_timeout 360 -verbose -httpd_conf /etc/httpd/conf/httpd.conf
perl t/TEST -run-tests || {
perl t/TEST -stop-httpd
    exit 1
}
perl t/TEST -stop-httpd
# in case of failures, see http://perl.apache.org/docs/2.0/user/help/help.html#_C_make_test___Failures
# then, debug like this:
# t/TEST -start-httpd
# tail -F t/logs/*&
# t/TEST -run-tests -verbose $failed_test
# t/TEST -stop-httpd

#make \
#    APACHE_TEST_PORT=select \
#    APACHE_TEST_STARTUP_TIMEOUT=30 \
#    APACHE_TEST_COLOR=1 \
#    TEST_VERBOSE=1 \
#    APACHE_TEST_HTTPD=%{_sbindir}/httpd \
#    APACHE_TEST_APXS=%{_sbindir}/apxs \
#    test

%endif

# make some directories
install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d
#install -d %{buildroot}%{_sysconfdir}/httpd/conf/addon-modules
install -d %{buildroot}%{_var}/www/perl

%makeinstall_std \
    MODPERL_AP_LIBEXECDIR=%{_libdir}/apache-extramodules \
    MODPERL_AP_INCLUDEDIR=%{_includedir}/apache \
    INSTALLDIRS=vendor

install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

# Remove empty file
rm -f docs/api/mod_perl-2.0/pm_to_blib

install -m0755 %{SOURCE3} %{buildroot}%{_var}/www/perl

# install missing required files
install -d %{buildroot}%{perl_vendorarch}/Apache2/Apache
install -m0644 xs/tables/current/Apache2/ConstantsTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/FunctionTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/StructureTable.pm %{buildroot}%{perl_vendorarch}/Apache2/Apache/

# cleanup
find %{buildroot}%{perl_archlib} -name perllocal.pod | xargs rm -f

# don't pack the Apache-Test stuff
rm -rf %{buildroot}%{perl_vendorlib}/Apache
rm -f %{buildroot}%{perl_vendorlib}/Bundle/ApacheTest.pm
rm -f %{buildroot}%{_mandir}/man3/Apache::Test*
rm -f %{buildroot}%{_mandir}/man3/Bundle::ApacheTest.3pm

# do not ship the patch backups                                                 
find %{buildroot}%{perl_vendorlib} -name '*.pm.cve*' | xargs rm -f

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
        %{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files -n %{name}
%defattr(-,root,root)
%doc Changes INSTALL LICENSE README docs todo
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
%{perl_vendorlib}
%{_mandir}/*/*
%attr(0755,root,root) %{_var}/www/perl/*.pl

%files devel
%defattr(-,root,root)
%attr(0755,root,root) %{_bindir}/*
%{_includedir}/apache/*
