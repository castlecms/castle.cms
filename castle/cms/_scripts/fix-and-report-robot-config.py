import argparse
import transaction
import os
import plone.api as api

from zope.component.hooks import setSite
import csv
from decimal import Decimal
from castle.cms.behaviors.search import ISearch


parser = argparse.ArgumentParser(description='Fix any issues with None values in existing robot configs, and run a report on current values at the same time')  # noqa: E501
parser.add_argument('--site-id', dest='site_id', required=True)
parser.add_argument('--dir-path', dest='dir_path', required=True)
parser.add_argument('--file-name', dest='file_name', default='robot-report.csv')
parser.add_argument('--commit', dest='should_commit', type=bool, default=False)
parser.add_argument('--batch-size', dest='batch_size', type=int, default=50)

parsed_args, _ = parser.parse_known_args()

NO_VALUE = '<NO_VALUE>'


class FileExistsError(Exception):
    pass


def get_physical_path(content_object):
    path_segments = [
        segment
        for segment in content_object.getPhysicalPath()
    ]
    public_url = api.portal.get_registry_record('plone.public_url', None)
    if public_url:
        path_segments = [public_url] + path_segments[2:]
    return '/'.join(path_segments)


def get_status_info(content_object):
    return {
        'physical_path': get_physical_path(content_object),
        'workflow_state': api.content.get_state(content_object),
        'robot_configuration': getattr(
            content_object,
            'robot_configuration',
            NO_VALUE,
        ),
        'robot_configuration_reset': False,
        'backend_robot_configuration': getattr(
            content_object,
            'backend_robot_configuration',
            NO_VALUE,
        ),
        'backend_robot_configuration_reset': False,
    }


def fix_robot_configs():
    report_data = []
    catalog = api.portal.get_tool('portal_catalog')
    content_object_brains = catalog.unrestrictedSearchResults(
        object_provides=ISearch.__identifier__,
    )
    content_object_count = len(content_object_brains)
    print('Found {} content objects to process'.format(content_object_count))
    current_index = 0
    for content_object_brain in content_object_brains:
        try:
            content_object = content_object_brain.getObject()
            content_status_info = get_status_info(content_object)

            for robot_key in ['robot_configuration', 'backend_robot_configuration']:
                current_value = content_status_info[robot_key]

                # this means the value is present but is not a list - that's the only scenario that's bad
                if not isinstance(current_value, list) and current_value != NO_VALUE:
                    try:
                        delattr(content_object, robot_key)
                        content_status_info[robot_key] = NO_VALUE
                        content_status_info[robot_key + '_reset'] = True

                        # now show what the new rendered value on the object is
                        if content_status_info[robot_key] == NO_VALUE:
                            content_status_info[robot_key] = getattr(
                                content_object,
                                robot_key,
                                '<THIS COULD BE A PROBLEM>',
                            ),
                        print('Fixed {robot_key} for {obj} with value {configuration_value}'.format(
                            robot_key=robot_key,
                            obj=content_object,
                            configuration_value=content_status_info[robot_key],
                        ))
                    except Exception:
                        print(
                            'Could not delete {robot_key} for {obj} with value {configuration_value}'.format(
                                robot_key=robot_key,
                                obj=content_object,
                                configuration_value=content_status_info[robot_key],
                            )
                        )
                        continue
        except Exception:
            print('Something very unexpected went wrong handling {}. Continuing'.format(
                content_object_brain.getPath()
            ))
            continue

        report_data.append(content_status_info)
        current_index += 1
        commit_action = 'Committing' if parsed_args.should_commit is True else 'Not committing'
        if current_index % parsed_args.batch_size == 0:
            print(
                '{percentage}% Complete ({current_index} of {total_count} objects processed). {commit_action}.'.format(  # noqa: E501
                    percentage=round(Decimal(current_index) / Decimal(content_object_count) * 100, 2),
                    current_index=current_index,
                    total_count=content_object_count,
                    commit_action=commit_action,
                )
            )

            if parsed_args.should_commit is True:
                transaction.commit()
    print('100% Complete ({total_count} of {total_count} objects processed). {commit_action}.'.format(
        total_count=content_object_count,
        commit_action=commit_action,
    ))

    if parsed_args.should_commit is True:
        transaction.commit()

    reset_item_paths = [
        item_info['physical_path']
        for item_info in report_data
        if item_info['robot_configuration_reset'] or item_info['backend_robot_configuration_reset']
    ]

    print(
        'Done fixing robot configs for {total_count} objects. {reset_count} objects reset: {reset_item_paths}'.format(  # noqa: E501
            total_count=content_object_count,
            reset_count=len(reset_item_paths),
            reset_item_paths=reset_item_paths,
        )
    )
    return report_data


def get_csv_report_row(report_row_data):
    return [
        report_row_data['physical_path'],
        report_row_data['workflow_state'],
        report_row_data['robot_configuration'],
        report_row_data.get('robot_configuration_reset', False),
        report_row_data['backend_robot_configuration'],
        report_row_data.get('backend_robot_configuration_reset', False),
    ]


def get_target_file_path():
    return os.path.join(parsed_args.dir_path, parsed_args.file_name)


def verify_target_file_does_not_exist():
    if os.path.exists(get_target_file_path()):
        raise FileExistsError


def write_report(report_data):
    file_path = get_target_file_path()
    print('Writing report to ' + file_path)
    with open(file_path, 'wb') as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                'physical_path',
                'workflow_state',
                'robot_configuration',
                'robot_configuration_reset',
                'backend_robot_configuration',
                'backend_robot_configuration_reset',
            ],
        )
        csv_writer.writeheader()
        csv_writer.writerows(report_data)
    print('Finished writing report')


if __name__ == '__main__':
    verify_target_file_does_not_exist()
    site = app[parsed_args.site_id]  # noqa: F821
    setSite(site)
    report_data = fix_robot_configs()
    write_report(report_data)
    print("That's all folks! We hope you've enjoyed your scripting experience.")
