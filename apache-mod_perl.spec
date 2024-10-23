%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}perl\\(Apache::TestConfig\\)
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}perl\\(Apache::TestReportPerl\\)
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}perl\\(Apache::TestRunPerl\\)
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}perl\\(Apache::TestTrace\\)

%define debug_package %{nil}

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

%define apache_version 2.4.62
%define mod_name mod_perl

Name:       apache-%{mod_name}
Version:    2.0.13
Release:    1
Summary:    An embedded Perl interpreter for the apache Web server
Group:      System/Servers
License:    Apache License
Url:        https://perl.apache.org/
Source0:    https://dlcdn.apache.org/perl/mod_perl-%{version}.tar.gz
Source1:    https://dlcdn.apache.org/perl/mod_perl-%{version}.tar.gz.sha512
Source2:    perl.conf
Source3:    perl.module.conf
Patch0:     mod_perl-2.0.4-inline.patch
BuildRequires: perl-devel >= 5.8.2
BuildRequires: perl(Tie::IxHash)
BuildRequires: perl(Data::Flow)
BuildRequires: perl-ExtUtils-Embed
BuildRequires: perl-Test
BuildRequires: apache >= %{apache_version}
BuildRequires: gdbm-devel
BuildRequires: pkgconfig(uuid)
%if %{build_test}
BuildRequires: perl-CGI >= 1:3.08
BuildRequires: perl-HTML-Parser
BuildRequires: perl-libwww-perl
BuildRequires: perl-URI
BuildRequires: perl-BSD-Resource
BuildRequires: apache-mod_cache >= %{apache_version}
BuildRequires: apache-mod_dav >= %{apache_version}
BuildRequires: apache-mod_deflate >= %{apache_version}
BuildRequires: apache-mod_disk_cache >= %{apache_version}
BuildRequires: apache-mod_file_cache >= %{apache_version}
BuildRequires: apache-mod_ldap >= %{apache_version}
BuildRequires: apache-mod_proxy >= %{apache_version}
BuildRequires: apache-mod_ssl >= %{apache_version}
BuildRequires: apache-mod_suexec >= %{apache_version}
BuildRequires: apache-mod_userdir >= %{apache_version}
%endif
BuildRequires: locales-extra-charsets
BuildRequires: apache-devel >= %{apache_version}
Requires:   apache >= %{apache_version}
Provides:   perl(mod_perl)
Provides:   perl(mod_perl2)
Epoch:      1

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
Summary:    Files needed for building XS modules that use mod_perl
Group:      Development/C
Requires:   %{name} = 1:%{version}-%{release}
Requires:   apache-devel >= %{apache_version}
Epoch:      1

%description	devel
The mod_perl-devel package contains the files needed for building XS
modules that use mod_perl.

%prep

%setup -q -n %{mod_name}-%{version}
%autopatch -p1

%build

for i in Changes SVN-MOVE; do
    iconv --from=ISO-8859-1 --to=UTF-8 $i > $i.utf8
    mv $i.utf8 $i
done

cd docs
for i in devel/debug/c.pod devel/core/explained.pod user/Changes.pod; do
    iconv --from=ISO-8859-1 --to=UTF-8 $i > $i.utf8
    mv $i.utf8 $i
done
cd ..

export CFLAGS="$RPM_OPT_FLAGS -fpic"

%{__perl} Makefile.PL \
    PREFIX=%{_prefix} \
    #MP_APXS=%{_httpd_apxs} \
    #MP_APR_CONFIG=%{_bindir}/apr-1-config \
    INSTALLDIRS=vendor \
    </dev/null

%make -C src/modules/perl OPTIMIZE="$RPM_OPT_FLAGS -fpic"
%make

%install
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
#    APACHE_TEST_APXS=%{_bindir}/apxs \
#    test

%endif

install -d %{buildroot}%{_httpd_moddir}
%makeinstall_std \
    MODPERL_AP_LIBEXECDIR=%{_httpd_moddir} \
    MODPERL_AP_INCLUDEDIR=%{_includedir}/httpd \
    INSTALLDIRS=vendor

# install config file
install -d -m 755 %{buildroot}%{_httpd_extconfdir}
install -d -m 755 %{buildroot}%{_httpd_modconfdir}
install -p -m 644 %{SOURCE2} %{buildroot}%{_httpd_extconfdir}
install -p -m 644 %{SOURCE3} %{buildroot}%{_httpd_modconfdir}/02-perl.conf

# install missing required files
install -d %{buildroot}%{perl_vendorarch}/Apache2/Apache
install -m0644 xs/tables/current/Apache2/ConstantsTable.pm \
    %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/FunctionTable.pm \
    %{buildroot}%{perl_vendorarch}/Apache2/Apache/
install -m0644 xs/tables/current/Apache2/StructureTable.pm \
    %{buildroot}%{perl_vendorarch}/Apache2/Apache/

# cleanup
find %{buildroot}%{perl_archlib} -name perllocal.pod | xargs rm -f

# don't pack the Apache-Test stuff
rm -rf %{buildroot}%{perl_vendorarch}/Apache/Test*
rm -rf %{buildroot}%{perl_vendorarch}/MyTest
rm -f %{buildroot}%{perl_vendorarch}/Bundle/ApacheTest.pm
rm -f %{buildroot}%{_mandir}/man3/Apache::Test*
rm -f %{buildroot}%{_mandir}/man3/Bundle::ApacheTest.3pm

%files
%doc BRANCHING Changes INSTALL LICENSE META.yml NOTICE README RELEASE STATUS
#config(noreplace) %{_httpd_extconfdir}/perl.conf
#config(noreplace) %{_httpd_modconfdir}/02-perl.conf
%{_bindir}/*
#{_httpd_moddir}/mod_perl.so
%{perl_vendorarch}/Apache
%{perl_vendorarch}/Apache2
%{perl_vendorarch}/Bundle
%{perl_vendorarch}/ModPerl
%{perl_vendorarch}/APR
%{perl_vendorarch}/APR.pm
%{perl_vendorarch}/mod_perl2.pm
%{perl_vendorarch}/auto/Apache2
%{perl_vendorarch}/auto/ModPerl
%{perl_vendorarch}/auto/APR
%{_mandir}/*/*

%files devel
%{_includedir}/httpd/*
